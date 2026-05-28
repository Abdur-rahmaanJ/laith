import re
import os
from typing import Dict, List, Optional, Set, Tuple, Union
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop,
    NavigatorPush, NavigatorPop,
    IRClass, IRField, IRMethod, ClassInit, AttributeGet, AttributeSet, MethodCall,
    Jump, Branch, IRIf, TryExcept, Raise
)
from laith.compiler.backend.kotlin.mapping import map_type_to_kotlin

def snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])

def readable_name(val_id: str, name_registry: Dict[str, str]) -> str:
    if val_id.startswith("fun_ref_"):
        return val_id.replace("fun_ref_", "")
    if val_id in name_registry:
        return name_registry[val_id]
    if val_id in {"context", "item", "newVal", "new_val", "granted", "lat", "lon"}:
        return val_id
    if val_id in {"void", "self"}:
        return val_id
    if val_id[0].isupper() and val_id not in name_registry:
        return val_id
    return f"v_{val_id}"

class KotlinEmitter:
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.global_values = set()
        self.current_func_is_ui = False
        self.in_ui_lambda = False
        self.current_self_id = None
        self.current_class_name = None
        self.source_map: List[Tuple[int, int]] = []
        self.final_source_map: List[Tuple[int, int]] = []
        self.ui_functions: Set[str] = set()
        self.needs_context: Set[str] = {"vibrate", "get_location", "request_location_permission"}
        self._needs_local_context = False
        self._has_unused_result = False
        self.name_registry: Dict[str, str] = {}
        self._deep_link_routes: List[Dict[str, str]] = []
        self.imports = {
            "laith.runtime.*",
            "kotlinx.coroutines.*",
            "kotlinx.coroutines.flow.*",
            "androidx.compose.runtime.*",
            "androidx.compose.ui.platform.LocalContext",
            "androidx.compose.foundation.layout.*",
            "androidx.compose.material3.*",
            "androidx.compose.ui.Modifier",
        }

    def _indent(self): return "    " * self.indent_level
    def _write(self, text: str, inst: Optional[IRInstruction] = None):
        line = f"{self._indent()}{text}"
        if inst and inst.source_line:
            line = f"{line} // from Python line {inst.source_line}"
        self.output.append(line)
        if inst and inst.source_line:
            self.source_map.append((len(self.output), inst.source_line))

    def _register_name(self, val: IRValue, hint: Optional[str] = None):
        if val.id not in self.name_registry and val.id != self.current_self_id:
            if hint:
                self.name_registry[val.id] = hint
            elif val.id in {"True", "False", "None", "void", "context", "self"}:
                self.name_registry[val.id] = val.id
            else:
                self.name_registry[val.id] = f"v_{val.id}"

    def reset(self):
        self.output = []
        self.indent_level = 0
        self.global_values = set()
        self.current_func_is_ui = False
        self.in_ui_lambda = False
        self.current_self_id = None
        self.current_class_name = None
        self.source_map = []
        self.final_source_map = []
        self.ui_functions = set()
        self._needs_local_context = False
        self._has_unused_result = False
        self.name_registry = {}
        self._deep_link_routes = []
        self.imports = {
            "laith.runtime.*",
            "kotlinx.coroutines.*",
            "kotlinx.coroutines.flow.*",
            "androidx.compose.runtime.*",
            "androidx.compose.ui.platform.LocalContext",
            "androidx.compose.foundation.layout.*",
            "androidx.compose.material3.*",
            "androidx.compose.ui.Modifier",
        }
        return self

    def emit(self, module: IRModule) -> str:
        self.native_func_names = {f.name for f in module.functions if any(d["name"] == "native" for d in f.decorators)}
        for cls in module.classes:
            for m in cls.methods:
                if any(d["name"] == "native" for d in m.decorators): self.native_func_names.add(m.name)

        self._infer_ui_functions(module)
        global_init = next((f for f in module.functions if f.name == "global_init"), None)
        if global_init:
            for b in global_init.blocks:
                for i in b.instructions:
                    if i.result: self.global_values.add(i.result.id)
                    self.visit_top_level_instruction(i)
            self.output.append("")
        for cls in module.classes: self.visit_class(cls); self.output.append("")
        for func in module.functions:
            if func.name == "global_init": continue
            self.visit_function(func); self.output.append("")
        self._emit_scheduler(module); self._emit_native_lib(module); self._emit_navigator(module); self._emit_http_helper(module); self._emit_resource_helper(module)
        header = [f"import {imp}" for imp in sorted(list(self.imports))]; header.append("")
        self.final_source_map = [(out_l + len(header), in_l) for out_l, in_l in self.source_map]
        return "\n".join(header + self.output)

    def _infer_ui_functions(self, module: IRModule):
        changed = True
        while changed:
            changed = False
            for f in module.functions:
                if f.name not in self.ui_functions and self._check_is_composable(f):
                    self.ui_functions.add(f.name); changed = True
            for cls in module.classes:
                for m in cls.methods:
                    name = f"{cls.name}.{m.name}"
                    if name not in self.ui_functions and self._check_is_composable(m):
                        self.ui_functions.add(name); changed = True

    def _check_is_composable(self, func: Union[IRFunction, IRMethod]) -> bool:
        def check_block(block: IRBlock) -> bool:
            for i in block.instructions:
                if isinstance(i, UICall): return True
                if isinstance(i, Call) and i.func_name in self.ui_functions: return True
                if isinstance(i, IRIf):
                    if check_block(i.then_block): return True
                    if i.else_block and check_block(i.else_block): return True
                if isinstance(i, TryExcept):
                    if check_block(i.body): return True
                    if check_block(i.handler): return True
            return False
        return any(check_block(b) for b in func.blocks)

    def get_source_map(self) -> List[Tuple[int, int]]: return self.final_source_map
    def visit_class(self, cls: IRClass):
        self.current_class_name = cls.name
        self._write(f"class {cls.name} {{")
        self.indent_level += 1
        for field in cls.fields: self._write(f"var {field.name}: Any? = null")
        for method in cls.methods: self.visit_method(method)
        self.indent_level -= 1; self._write("}"); self.current_class_name = None

    def visit_method(self, method: IRMethod):
        is_ui = f"{self.current_class_name}.{method.name}" in self.ui_functions
        camel_name = snake_to_camel(method.name)
        if is_ui: self._write("@Composable")
        params = []
        for a in method.args[1:]:
            self._register_name(a, a.id)
            params.append(f"{self._v(a)}: {map_type_to_kotlin(a.type)}")
        comment = f" // from Python: {method.name}" if method.name != camel_name else ""
        self._write(f"{'suspend ' if method.is_async else ''}fun {camel_name}({', '.join(params)}): {map_type_to_kotlin(method.return_type)} {{{comment}")
        self.indent_level += 1
        if len(method.args) > 0: self.current_self_id = method.args[0].id; self._write(f"val {self._v(method.args[0])} = this")
        prev_ui = self.current_func_is_ui; self.current_func_is_ui = is_ui
        if is_ui:
            self._write("val context = LocalContext.current")
            for block in method.blocks: self.visit_block(block)
        else:
            for block in method.blocks: self.visit_block(block)
        self.indent_level -= 1; self._write("}")
        self.current_func_is_ui = prev_ui; self.current_self_id = None

    def visit_function(self, func: IRFunction):
        is_ui = func.name in self.ui_functions
        camel_name = snake_to_camel(func.name)
        route_decorator = next((d for d in func.decorators if d["name"] == "route"), None)
        if route_decorator:
            route_path = route_decorator["args"].get("path", f"/{camel_name}")
            self._write(f"@Route(\"{route_path}\")")
        perm_decorator = next((d for d in func.decorators if d["name"] == "requires_permission"), None)
        is_restricted = perm_decorator is not None
        if is_ui: self._write("@Composable")
        params = []
        for a in func.args:
            self._register_name(a, a.id)
            params.append(f"{self._v(a)}: {map_type_to_kotlin(a.type)}")
        comment = f" // from Python: {func.name}" if func.name != camel_name else ""
        self._write(f"{'suspend ' if func.is_async else ''}fun {camel_name}({', '.join(params)}): {map_type_to_kotlin(func.return_type)} {{{comment}")
        self.indent_level += 1
        prev_ui = self.current_func_is_ui; self.current_func_is_ui = is_ui
        if is_restricted:
            perm_name = perm_decorator["args"].get("0") or perm_decorator["args"].get("permission", "")
            android_perm = f"android.Manifest.permission.{perm_name}" if not perm_name.startswith("android.") else perm_name
            self.imports.add("android.content.pm.PackageManager")
            self.imports.add("androidx.core.content.ContextCompat")
            self._needs_local_context = True
            self._write("val context = LocalContext.current")
            self._write(f"if (ContextCompat.checkSelfPermission(context, {android_perm}) != PackageManager.PERMISSION_GRANTED) {{")
            self.indent_level += 1
            self._write("// Permission not granted — request it")
            self._write(f"ActivityResultContracts.RequestPermission()")
            self.indent_level -= 1
            self._write("}")
        if is_ui:
            if not is_restricted:
                self._write("val context = LocalContext.current")
            for block in func.blocks: self.visit_block(block)
        else:
            if not is_restricted: self._write("val context = laith.runtime.LaithContext.current")
            for block in func.blocks: self.visit_block(block)
        self.indent_level -= 1; self._write("}")
        self.current_func_is_ui = prev_ui

    def _emit_scheduler(self, module: IRModule):
        self._write("fun scheduleLaithTasks(context: android.content.Context) { laith.runtime.LaithContext.current = context }")
    def _emit_native_lib(self, module: IRModule): self._write("object NativeLib { init { System.loadLibrary(\"laith-native\") } }")

    def _needs_navigator(self, module: IRModule) -> bool:
        for func in module.functions:
            for block in func.blocks:
                for inst in block.instructions:
                    if isinstance(inst, (NavigatorPush, NavigatorPop)):
                        return True
        for cls in module.classes:
            for method in cls.methods:
                for block in method.blocks:
                    for inst in block.instructions:
                        if isinstance(inst, (NavigatorPush, NavigatorPop)):
                            return True
        return False

    def _get_routes(self, module: IRModule) -> List[tuple[str, str, Optional[str], Optional[str]]]:
        routes = []
        for func in module.functions:
            route_dec = next((d for d in func.decorators if d["name"] == "route"), None)
            if route_dec:
                path = route_dec["args"].get("path", f"/{snake_to_camel(func.name)}")
                scheme = route_dec["args"].get("scheme")
                host = route_dec["args"].get("host")
                routes.append((path, snake_to_camel(func.name), scheme, host))
        return routes

    def get_deep_link_routes(self) -> List[Dict[str, str]]:
        return self._deep_link_routes

    def _emit_navigator(self, module: IRModule):
        if not self._needs_navigator(module):
            return
        self.imports.add("androidx.navigation.compose.*")
        self.imports.add("androidx.navigation.compose.rememberNavController")
        routes = self._get_routes(module)
        has_deep_links = any(scheme for _, _, scheme, _ in routes)
        if has_deep_links:
            self.imports.add("androidx.navigation.navDeepLink")
        self._write("")
        self._write("// Navigation infrastructure")
        self._write("@Composable")
        self._write("fun LaithNavHost(navController: NavHostController) {")
        self.indent_level += 1
        self._write("NavHost(navController = navController, startDestination = \"" + (routes[0][0] if routes else "/") + "\") {")
        self.indent_level += 1
        for path, func_name, scheme, host in routes:
            if scheme:
                uri_pattern = f"{scheme}://{host or 'laith.app'}{path}"
                self._write(f"composable(\"{path}\", deepLinks = listOf(navDeepLink {{ uriPattern = \"{uri_pattern}\" }})) {{ {func_name}() }}")
            else:
                self._write(f"composable(\"{path}\") {{ {func_name}() }}")
        self.indent_level -= 1
        self._write("}")
        self.indent_level -= 1
        self._write("}")
        self._deep_link_routes = [
            {"scheme": scheme, "host": host or "laith.app", "path": path}
            for path, _, scheme, host in routes if scheme
        ]
        self._write("")
        self._write("fun navigatorPush(screen: String) {")
        self.indent_level += 1
        self._write("// Screen push handled by NavHostController.navigate")
        self.indent_level -= 1
        self._write("}")
        self._write("")
        self._write("fun navigatorPop() {")
        self.indent_level += 1
        self._write("// Screen pop handled by NavHostController.popBackStack")
        self.indent_level -= 1
        self._write("}")

    def _emit_http_helper(self, module: IRModule):
        if not self._uses_http(module):
            return
        self.imports.add("java.net.HttpURLConnection")
        self.imports.add("java.net.URL")
        self._write("")
        self._write("// HTTP client support")
        self._write("data class HttpResponse(val code: Int, val body: String) {")
        self.indent_level += 1
        self._write("val text: String get() = body")
        self._write("val statusCode: Int get() = code")
        self._write("fun json(): org.json.JSONObject = org.json.JSONObject(body)")
        self._write("fun jsonArray(): org.json.JSONArray = org.json.JSONArray(body)")
        self.indent_level -= 1
        self._write("}")

    def _uses_http(self, module: IRModule) -> bool:
        for func in module.functions:
            for block in func.blocks:
                for inst in block.instructions:
                    if isinstance(inst, MethodCall) and hasattr(inst.obj, 'type') and inst.obj.type.name == "laith.HttpClient":
                        return True
        return False

    def _emit_resource_helper(self, module: IRModule):
        if not self._uses_resource(module):
            return
        self._write("")
        self._write("// Resource pattern for async data loading")
        self._write("class Resource<T>(private val fetcher: suspend () -> T) {")
        self.indent_level += 1
        self._write("var data: T? = null")
        self._write("var loading: Boolean = false")
        self._write("var error: String? = null")
        self._write("private var job: kotlinx.coroutines.Job? = null")
        self._write("")
        self._write("fun load() {")
        self.indent_level += 1
        self._write("job?.cancel()")
        self._write("loading = true")
        self._write("error = null")
        self._write("job = kotlinx.coroutines.GlobalScope.launch {")
        self.indent_level += 1
        self._write("try { data = fetcher() } catch (e: Exception) { error = e.message } finally { loading = false }")
        self.indent_level -= 1
        self._write("}")
        self.indent_level -= 1
        self._write("}")
        self._write("")
        self._write("fun retry() { load() }")
        self._write("fun cancel() { job?.cancel(); loading = false }")
        self._write("")
        self._write("init { load() }")
        self.indent_level -= 1
        self._write("}")
        self.imports.add("kotlinx.coroutines.GlobalScope")
        self.imports.add("kotlinx.coroutines.launch")

    def _uses_resource(self, module: IRModule) -> bool:
        for func in module.functions:
            for block in func.blocks:
                for inst in block.instructions:
                    if isinstance(inst, Call) and inst.func_name == "resource":
                        return True
        return False

    def visit_top_level_instruction(self, inst: IRInstruction):
        if isinstance(inst, Constant):
            val = inst.value
            if isinstance(val, str): val = f'"{val}"'
            elif isinstance(val, bool): val = str(val).lower()
            self._write(f"val {self._v(inst.result)} = {val}", inst)
        elif isinstance(inst, ClassInit):
            args = ", ".join(self._v(a) for a in inst.args)
            self._write(f"val {self._v(inst.result)} = {inst.class_name}().apply {{ __init__({args}) }}", inst)
        elif isinstance(inst, StateInit):
            self._write(f"val {self._v(inst.result)} = MutableStateFlow<Any?>({self._v(inst.initial_value)})", inst)
            self.imports.add("kotlinx.coroutines.flow.MutableStateFlow")

    def _v(self, val: IRValue) -> str:
        return readable_name(val.id, self.name_registry)

    def visit_block(self, block: IRBlock):
        for inst in block.instructions: self.visit_instruction(inst)

    def visit_instruction(self, inst: IRInstruction):
        if isinstance(inst, Constant):
            v = inst.value
            if isinstance(v, str): val = f'"{str(v).replace('"', '\\"').replace("\n", "\\n")}"'
            elif isinstance(v, bool): val = str(v).lower()
            else: val = str(v)
            self._write(f"val {self._v(inst.result)} = {val}", inst)
        elif isinstance(inst, BinaryOp):
            op_map = {"add": "+", "sub": "-", "mul": "*", "div": "/", "lt": "<", "gt": ">", "eq": "==", "ne": "!=", "le": "<=", "ge": ">="}
            op = op_map.get(inst.op, inst.op)
            l, r = self._v(inst.left), self._v(inst.right)
            if inst.op == "add": self._write(f"val {self._v(inst.result)} = \"${{({l} ?: \"\")}} ${{({r} ?: \"\")}} \".trim()", inst)
            else:
                le, re = f"({l} as? Number)?.toInt() ?: 0", f"({r} as? Number)?.toInt() ?: 0"
                if inst.op in ["eq", "ne"]: self._write(f"val {self._v(inst.result)} = ({l} == {r})", inst)
                else: self._write(f"val {self._v(inst.result)} = {le} {op} {re}", inst)
        elif isinstance(inst, Call):
            if inst.func_name in ["get_location", "request_location_permission"]:
                 self._needs_local_context = True
                 cb = inst.args[0] if len(inst.args) > 0 and isinstance(inst.args[0], IRBlock) else None
                 if inst.func_name == "get_location": self._write("PythonRuntime.getLastLocation(context) { lat, lon ->", inst)
                 else: self._write("PythonRuntime.requestLocationPermission(context) { granted ->", inst)
                 if cb: self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1
                 self._write("}"); return
            if inst.func_name == "effect":
                state_val = inst.args[0] if inst.args and isinstance(inst.args[0], IRValue) else None
                cb = inst.args[1] if len(inst.args) > 1 and isinstance(inst.args[1], IRBlock) else None
                self.imports.add("androidx.compose.runtime.LaunchedEffect")
                self.imports.add("kotlinx.coroutines.flow.collect")
                if state_val:
                    key = self._v(state_val)
                    self._write(f"val v_effectKey = {key}", inst)
                    self._write(f"LaunchedEffect(v_effectKey) {{", inst)
                else:
                    self._write("LaunchedEffect(Unit) {", inst)
                if cb:
                    self.indent_level += 1
                    self._write(f"val newVal = {self._v(state_val)}" if state_val else "")
                    self.visit_block(cb)
                    self.indent_level -= 1
                self._write("}"); return
            if inst.func_name == "remember_permission":
                perm_name = self._v(inst.args[0]) if inst.args else "null"
                self.imports.add("androidx.compose.runtime.remember")
                self.imports.add("androidx.compose.runtime.mutableStateOf")
                self.imports.add("androidx.core.content.ContextCompat")
                self.imports.add("android.content.pm.PackageManager")
                self._needs_local_context = True
                self._write(f"val {self._v(inst.result)} = remember {{", inst)
                self.indent_level += 1
                self._write("val granted = ContextCompat.checkSelfPermission(context,")
                self._write(f"    android.Manifest.permission.{perm_name.replace('\"', '')}) == PackageManager.PERMISSION_GRANTED")
                self._write(f"mutableStateOf(granted)")
                self.indent_level -= 1
                self._write("}", inst)
                return
            if inst.func_name == "on_mount":
                cb = inst.args[0] if inst.args and isinstance(inst.args[0], IRBlock) else None
                self.imports.add("androidx.compose.runtime.LaunchedEffect")
                self._write("LaunchedEffect(Unit) {", inst)
                if cb: self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1
                self._write("}"); return
            if inst.func_name == "on_dispose":
                cb = inst.args[0] if inst.args and isinstance(inst.args[0], IRBlock) else None
                self.imports.add("androidx.compose.runtime.DisposableEffect")
                self._write("DisposableEffect(Unit) {", inst)
                self.indent_level += 1
                if cb: self._write("onDispose {"); self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1; self._write("}")
                self.indent_level -= 1; self._write("}"); return
            if inst.func_name == "on_resume":
                cb = inst.args[0] if inst.args and isinstance(inst.args[0], IRBlock) else None
                self.imports.add("androidx.compose.runtime.LaunchedEffect")
                self.imports.add("androidx.lifecycle.Lifecycle")
                self.imports.add("androidx.lifecycle.LifecycleEventObserver")
                self.imports.add("androidx.lifecycle.compose.LocalLifecycleOwner")
                self._write("val lifecycleOwner = LocalLifecycleOwner.current", inst)
                self._write("DisposableEffect(lifecycleOwner) {", inst)
                self.indent_level += 1
                self._write("val observer = LifecycleEventObserver { _, event ->")
                self.indent_level += 1
                self._write("if (event == Lifecycle.Event.ON_RESUME) {")
                if cb: self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1
                self._write("}")
                self.indent_level -= 1
                self._write("}")
                self._write("lifecycleOwner.lifecycle.addObserver(observer)")
                self._write("onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }")
                self.indent_level -= 1; self._write("}"); return
            if inst.func_name == "on_pause":
                cb = inst.args[0] if inst.args and isinstance(inst.args[0], IRBlock) else None
                self.imports.add("androidx.lifecycle.Lifecycle")
                self.imports.add("androidx.lifecycle.LifecycleEventObserver")
                self.imports.add("androidx.lifecycle.compose.LocalLifecycleOwner")
                self._write("val lifecycleOwner = LocalLifecycleOwner.current", inst)
                self._write("DisposableEffect(lifecycleOwner) {", inst)
                self.indent_level += 1
                self._write("val observer = LifecycleEventObserver { _, event ->")
                self.indent_level += 1
                self._write("if (event == Lifecycle.Event.ON_PAUSE) {")
                if cb: self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1
                self._write("}")
                self.indent_level -= 1
                self._write("}")
                self._write("lifecycleOwner.lifecycle.addObserver(observer)")
                self._write("onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }")
                self.indent_level -= 1; self._write("}"); return
            if inst.func_name == "resource":
                func_arg = inst.args[0] if inst.args else None
                func_name = ""
                if func_arg and isinstance(func_arg, IRValue):
                    func_name = func_arg.id.replace("fun_ref_", "")
                self._write(f"val {self._v(inst.result)} = Resource({{", inst)
                self.indent_level += 1
                if func_name:
                    self._write(f"withContext(Dispatchers.IO) {{ {snake_to_camel(func_name)}() }}")
                self.indent_level -= 1
                self._write("})")
                self.imports.add("kotlinx.coroutines.withContext")
                self.imports.add("kotlinx.coroutines.Dispatchers")
                return
            if inst.func_name == "emptyList":
                if inst.result: self._write(f"val {self._v(inst.result)} = emptyList<Any?>()", inst)
                else: self._write("emptyList<Any?>()", inst)
                return
            if inst.func_name == "listOf":
                args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
                if inst.result: self._write(f"val {self._v(inst.result)} = listOf<Any?>({args})", inst)
                else: self._write(f"listOf<Any?>({args})", inst)
                return
            if inst.func_name == "emptyMap":
                if inst.result: self._write(f"val {self._v(inst.result)} = emptyMap<Any?, Any?>()", inst)
                else: self._write("emptyMap<Any?, Any?>()", inst)
                return
            if inst.func_name == "pairOf":
                a0 = self._v(inst.args[0]) if len(inst.args) > 0 else "null"
                a1 = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                if inst.result: self._write(f"val {self._v(inst.result)} = {a0} to {a1}", inst)
                else: self._write(f"{a0} to {a1}", inst)
                return
            if inst.func_name == "mapOf":
                args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
                if inst.result: self._write(f"val {self._v(inst.result)} = mapOf<Any?, Any?>({args})", inst)
                else: self._write(f"mapOf<Any?, Any?>({args})", inst)
                return
            args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
            camel_func = snake_to_camel(inst.func_name)
            if inst.func_name == "vibrate": self._needs_local_context = True; self._write(f"PythonRuntime.vibrate(context, ({args} as? Number)?.toLong() ?: 500L)", inst)
            elif inst.result: self._write(f"val {self._v(inst.result)} = {camel_func}({args})", inst)
            else: self._write(f"{camel_func}({args})", inst)
        elif isinstance(inst, MethodCall):
            args_str = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            if "." in inst.obj.type.name and inst.obj.type.name not in ("laith.HttpResponse", "laith.Resource") and obj == inst.obj.type.name.rsplit(".", 1)[-1]:
                obj = inst.obj.type.name
            safe = not self.current_func_is_ui and inst.obj.id == "context"
            if safe: self._needs_local_context = True
            op = "?" if safe else ""
            if inst.obj.type.name in ("laith.FileStorage", "FileStorage"):
                file_path = self._v(inst.args[0]) if inst.args else "null"
                self._needs_local_context = True
                if inst.method_name == "read_text":
                    self._write(f"val {self._v(inst.result)} = java.io.File(context.filesDir, {file_path}).readText()", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name == "write_bytes":
                    data = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"java.io.File(context.filesDir, {file_path}).writeBytes({data})", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name == "read_bytes":
                    self._write(f"val {self._v(inst.result)} = java.io.File(context.filesDir, {file_path}).readBytes()", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name == "write_text":
                    data = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"java.io.File(context.filesDir, {file_path}).writeText({data})", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name == "delete":
                    self._write(f"java.io.File(context.filesDir, {file_path}).delete()", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name == "exists":
                    self._write(f"val {self._v(inst.result)} = java.io.File(context.filesDir, {file_path}).exists()", inst)
                    self.imports.add("java.io.File")
                elif inst.method_name in ("get_cache_dir", "get_cache_dir", "getFilesDir", "getCacheDir"):
                    dir_type = "cacheDir" if "cache" in inst.method_name else "filesDir"
                    self._write(f"val {self._v(inst.result)} = context.{dir_type}.absolutePath", inst)
                else:
                    self._write(f"{obj}.{inst.method_name}({args_str})", inst)
            elif inst.obj.type.name == "laith.Preferences" or inst.obj.type.name == "Preferences":
                key = self._v(inst.args[0]) if inst.args else "null"
                if inst.method_name == "get":
                    default = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"val {self._v(inst.result)} = {obj}.getString({key}, {default}) ?: {default}", inst)
                elif inst.method_name == "set":
                    val = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"{obj}.edit().putString({key}, {val}.toString()).apply()", inst)
                elif inst.method_name == "remove":
                    self._write(f"{obj}.edit().remove({key}).apply()", inst)
                elif inst.method_name == "contains":
                    self._write(f"val {self._v(inst.result)} = {obj}.contains({key})", inst)
                else:
                    self._write(f"{obj}.{inst.method_name}({args_str})", inst)
            elif inst.obj.type.name == "laith.SecureStorage" or inst.obj.type.name == "SecureStorage":
                key = self._v(inst.args[0]) if inst.args else "null"
                if inst.method_name == "get":
                    default = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"val {self._v(inst.result)} = {obj}.getString({key}, {default}) ?: {default}", inst)
                elif inst.method_name == "set":
                    val = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    self._write(f"{obj}.edit().putString({key}, {val}.toString()).apply()", inst)
                elif inst.method_name == "remove":
                    self._write(f"{obj}.edit().remove({key}).apply()", inst)
                elif inst.method_name == "contains":
                    self._write(f"val {self._v(inst.result)} = {obj}.contains({key})", inst)
                else:
                    self._write(f"{obj}.{inst.method_name}({args_str})", inst)
            elif inst.obj.type.name == "laith.HttpClient" or inst.obj.id == "httpClient":
                http_method = inst.method_name.upper()
                url_val = self._v(inst.args[0]) if inst.args else "null"
                headers_val = "null"
                params_val = "null"
                json_val = "null"
                for k, v in inst.keywords.items():
                    kw = snake_to_camel(k)
                    if kw == "headers":
                        headers_val = self._v(v) if isinstance(v, IRValue) else "null"
                    elif kw == "params":
                        params_val = self._v(v) if isinstance(v, IRValue) else "null"
                    elif kw == "json":
                        json_val = self._v(v) if isinstance(v, IRValue) else "null"
                self._needs_local_context = True
                self.imports.add("kotlinx.coroutines.Dispatchers")
                self.imports.add("kotlinx.coroutines.withContext")
                self._write(f"val {self._v(inst.result)} = withContext(Dispatchers.IO) {{", inst)
                self.indent_level += 1
                self._write(f"val conn = java.net.URL({url_val}.toString()).openConnection() as java.net.HttpURLConnection")
                self._write(f"conn.requestMethod = \"{http_method}\"")
                self._write(f"conn.connectTimeout = 15000")
                self._write(f"conn.readTimeout = 15000")
                if headers_val != "null":
                    self._write(f"// headers = {headers_val}")
                if params_val != "null":
                    self._write(f"// params = {params_val}")
                if json_val != "null":
                    self._write(f"conn.doOutput = true")
                    self._write(f"conn.setRequestProperty(\"Content-Type\", \"application/json\")")
                    self._write(f"conn.outputStream.write({json_val}.toString().toByteArray())")
                self._write(f"val code = conn.responseCode")
                self._write(f"val body = conn.inputStream.bufferedReader().readText()")
                self._write(f"conn.disconnect()")
                self._write(f"HttpResponse(code, body)")
                self.indent_level -= 1; self._write("}")
            elif inst.obj.type.name == "laith.HttpResponse" or inst.obj.type.name == "HttpResponse":
                camel_method = snake_to_camel(inst.method_name)
                if inst.method_name == "json":
                    self._write(f"val {self._v(inst.result)} = {obj}.json()", inst)
                elif inst.method_name == "json_array" or camel_method == "jsonArray":
                    self._write(f"val {self._v(inst.result)} = {obj}.jsonArray()", inst)
                else:
                    self._write(f"val {self._v(inst.result)} = {obj}.{camel_method}({args_str})", inst)
            elif inst.obj.type.name == "laith.Database" or inst.obj.type.name == "Database":
                sql = self._v(inst.args[0]) if inst.args else '""'
                params = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args[1:])
                params_str = f", arrayOf({params})" if params else ""
                if inst.method_name == "query":
                    self._write(f"val {self._v(inst.result)} = {obj}.rawQuery({sql}{params_str})", inst)
                    self.imports.add("android.database.Cursor")
                elif inst.method_name == "execute":
                    self._write(f"{obj}.execSQL({sql}{params_str})", inst)
                elif inst.method_name == "close":
                    self._write(f"{obj}.close()", inst)
                elif inst.method_name == "delete":
                    table = self._v(inst.args[0]) if inst.args else '""'
                    where = self._v(inst.args[1]) if len(inst.args) > 1 else "null"
                    where_args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args[2:])
                    self._write(f"{obj}.delete({table}, {where}, arrayOf({where_args}))", inst)
                else:
                    self._write(f"{obj}.{inst.method_name}({args_str})", inst)
            elif inst.method_name == "set":
                v = self._v(inst.args[0])
                self._write(f"({obj} as? MutableStateFlow<Any?>)?.value = {v}", inst)
                self._write(f"({obj} as? MutableState<Any?>)?.value = {v}", inst)
            elif inst.result: self._write(f"val {self._v(inst.result)} = {obj}{op}.{inst.method_name}({args_str})", inst)
            else: self._write(f"{obj}{op}.{inst.method_name}({args_str})", inst)
        elif isinstance(inst, ClassInit):
            args = ", ".join(self._v(a) for a in inst.args)
            if inst.class_name == "Preferences":
                name_arg = self._v(inst.args[0]) if inst.args else '"app"'
                self._needs_local_context = True
                self._write(f"val {self._v(inst.result)} = context.getSharedPreferences({name_arg}, android.content.Context.MODE_PRIVATE)", inst)
                self.imports.add("android.content.Context")
            elif inst.class_name == "Database":
                db_name = self._v(inst.args[0]) if inst.args else '"app.db"'
                self._needs_local_context = True
                self._write(f"val {self._v(inst.result)} = context.openOrCreateDatabase({db_name}, Context.MODE_PRIVATE, null)", inst)
                self.imports.add("android.content.Context")
            elif inst.class_name == "SecureStorage":
                name_arg = self._v(inst.args[0]) if inst.args else '"secure_prefs"'
                self._needs_local_context = True
                self._write(f"val {self._v(inst.result)} = SecureStorageUtil.getInstance(context, {name_arg})", inst)
                self.imports.add("androidx.security.crypto.EncryptedSharedPreferences")
                self.imports.add("androidx.security.crypto.MasterKey")
            elif "." in inst.result.type.name: 
                 self._write(f"val {self._v(inst.result)} = {inst.result.type.name}({args})", inst)
            else: self._write(f"val {self._v(inst.result)} = {inst.class_name}().apply {{ __init__({args}) }}", inst)
        elif isinstance(inst, AttributeGet):
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            if "." in inst.obj.type.name and inst.obj.type.name not in ("laith.HttpResponse", "laith.Resource") and obj == inst.obj.type.name.rsplit(".", 1)[-1]:
                obj = inst.obj.type.name
            attr_name = inst.attr_name if inst.attr_name.isupper() else snake_to_camel(inst.attr_name)
            self._write(f"val {self._v(inst.result)} = {obj}.{attr_name}", inst)
        elif isinstance(inst, AttributeSet):
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            self._write(f"{obj}.{inst.attr_name} = {self._v(inst.value)}", inst)
        elif isinstance(inst, StateInit):
            v = self._v(inst.initial_value)
            if self.current_func_is_ui: self._write(f"val {self._v(inst.result)} = remember {{ mutableStateOf<Any?>({v}) }}", inst)
            else: self._write(f"val {self._v(inst.result)} = MutableStateFlow<Any?>({v})", inst)
        elif isinstance(inst, UICall):
            args = []
            pass_args = inst.func_name not in {"Button", "TextField", "Checkbox", "Switch", "Slider", "AndroidView"}
            if pass_args: args = [self._v(a) for a in inst.args]
            has_callback = False
            for k, v in inst.keywords.items():
                if isinstance(v, IRBlock):
                    has_callback = True
                else:
                    kw = "onClick" if k == "on_click" else snake_to_camel(k)
                    args.append(f"{kw} = {self._v(v)}")
            camel_func = snake_to_camel(inst.func_name)
            call = f"{camel_func}({', '.join(args)})"

            if inst.func_name == "Button":
                click_block = next((v for k, v in inst.keywords.items() if isinstance(v, IRBlock)), None)
                self._write("Button(onClick = {", inst)
                if click_block:
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(click_block); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}) {"); self.indent_level += 1
                if inst.args: self._write(f"Text({self._v(inst.args[0])}.toString())")
                self.indent_level -= 1; self._write("}")
            elif inst.func_name == "TextField":
                val = next((self._v(v) for k, v in inst.keywords.items() if k == "value"), "null")
                change_block = inst.keywords.get("on_value_change", None)
                if isinstance(change_block, IRBlock):
                    self._write(f"OutlinedTextField(value = {val}, onValueChange = {{ newVal ->", inst)
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(change_block); self.indent_level -= 1; self.in_ui_lambda = prev
                    self._write("})")
                else:
                    self._write(f"OutlinedTextField(value = {val}, onValueChange = {{}})", inst)
            elif inst.func_name == "Checkbox":
                checked = next((self._v(v) for k, v in inst.keywords.items() if k == "checked"), "false")
                change_block = inst.keywords.get("on_checked_change", None)
                if isinstance(change_block, IRBlock):
                    self._write(f"Checkbox(checked = {checked}, onCheckedChange = {{ newVal ->", inst)
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(change_block); self.indent_level -= 1; self.in_ui_lambda = prev
                    self._write("})")
                else:
                    self._write(f"Checkbox(checked = {checked}, onCheckedChange = null)", inst)
            elif inst.func_name == "Switch":
                checked = next((self._v(v) for k, v in inst.keywords.items() if k == "checked"), "false")
                change_block = inst.keywords.get("on_checked_change", None)
                if isinstance(change_block, IRBlock):
                    self._write(f"Switch(checked = {checked}, onCheckedChange = {{ newVal ->", inst)
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(change_block); self.indent_level -= 1; self.in_ui_lambda = prev
                    self._write("})")
                else:
                    self._write(f"Switch(checked = {checked}, onCheckedChange = null)", inst)
            elif inst.func_name == "Slider":
                val = next((self._v(v) for k, v in inst.keywords.items() if k == "value"), "0f")
                change_block = inst.keywords.get("on_value_change", None)
                if isinstance(change_block, IRBlock):
                    self._write(f"Slider(value = {val}, onValueChange = {{ newVal ->", inst)
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(change_block); self.indent_level -= 1; self.in_ui_lambda = prev
                    self._write("})")
                else:
                    self._write(f"Slider(value = {val}, onValueChange = {{}})", inst)
            elif inst.func_name == "Scaffold":
                scaffold_args = []
                kw_map = {"top_bar": "topBar", "bottom_bar": "bottomBar", "fab": "floatingActionButton"}
                for k, v in inst.keywords.items():
                    kw = kw_map.get(k, snake_to_camel(k))
                    if isinstance(v, IRValue):
                        scaffold_args.append(f"{kw} = {self._v(v)}")
                    elif isinstance(v, IRBlock):
                        scaffold_args.append(f"{kw} = {{ {self._v(next(iter(v.instructions), None)) if v.instructions else ''} }}")
                body = inst.keywords.get("body", None)
                if isinstance(body, IRBlock):
                    self._write(f"Scaffold({', '.join(scaffold_args)}) {{", inst)
                    self.indent_level += 1; self.visit_block(body); self.indent_level -= 1; self._write("}")
                else:
                    self._write(f"Scaffold({', '.join(scaffold_args)}) {{}}", inst)
            elif inst.func_name == "AndroidView":
                factory_block = inst.args[0] if inst.args and isinstance(inst.args[0], IRBlock) else None
                self.imports.add("androidx.compose.ui.viewinterop.AndroidView")
                if factory_block:
                    self._write("AndroidView(factory = { ctx ->", inst)
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(factory_block); self.indent_level -= 1; self.in_ui_lambda = prev
                    self._write("})", inst)
                else:
                    factory_arg = self._v(inst.args[0]) if inst.args else "{}"
                    self._write(f"AndroidView(factory = {factory_arg})", inst)
            elif inst.func_name == "Theme":
                primary = next((self._v(v) for k, v in inst.keywords.items() if k == "primary"), None)
                dark_primary = next((self._v(v) for k, v in inst.keywords.items() if k == "dark_primary"), None)
                use_dynamic = next((self._v(v) for k, v in inst.keywords.items() if k == "use_dynamic_colors"), None)
                self.imports.add("androidx.compose.material3.MaterialTheme")
                self.imports.add("androidx.compose.material3.lightColorScheme")
                self.imports.add("androidx.compose.material3.darkColorScheme")
                self.imports.add("androidx.compose.foundation.isSystemInDarkTheme")
                self._write("MaterialTheme(", inst)
                if use_dynamic:
                    self._write(f"    colorScheme = if (isSystemInDarkTheme()) {{")
                    self._write(f"        dynamicDarkColorScheme(LocalContext.current)")
                    self._write(f"    }} else {{")
                    self._write(f"        dynamicLightColorScheme(LocalContext.current)")
                    self._write(f"    }}")
                    self.imports.add("androidx.compose.material3.dynamicDarkColorScheme")
                    self.imports.add("androidx.compose.material3.dynamicLightColorScheme")
                elif primary or dark_primary:
                    self._write(f"    colorScheme = if (isSystemInDarkTheme()) {{")
                    dark = dark_primary or primary
                    self._write(f"        darkColorScheme(primary = Color(0xFF{dark.replace('#', '')}))")
                    self._write(f"    }} else {{")
                    self._write(f"        lightColorScheme(primary = Color(0xFF{primary.replace('#', '')}))")
                    self._write(f"    }}")
                if inst.body:
                    self._write(") {", inst)
                    self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1; self._write("}")
                else:
                    self._write(") { }", inst)
            elif inst.func_name == "Dialog":
                on_dismiss = inst.keywords.get("on_dismiss", None)
                has_dismiss = isinstance(on_dismiss, IRBlock)
                self._write("Dialog(onDismissRequest = {", inst)
                if has_dismiss:
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(on_dismiss); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}) {")
                if inst.body:
                    self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1
                self._write("}")
                self.imports.add("androidx.compose.ui.window.Dialog")
            elif inst.func_name == "AlertDialog":
                on_confirm = inst.keywords.get("on_confirm", None)
                on_dismiss = inst.keywords.get("on_dismiss", None)
                title_val = next((self._v(v) for k, v in inst.keywords.items() if k == "title"), "null")
                text_val = next((self._v(v) for k, v in inst.keywords.items() if k == "text"), "null")
                self._write(f"AlertDialog(onDismissRequest = {{", inst)
                if isinstance(on_dismiss, IRBlock):
                    self.indent_level += 1; self.visit_block(on_dismiss); self.indent_level -= 1
                self._write(f"}}, title = {{ Text({title_val}) }}, text = {{ Text({text_val}) }}", inst)
                if isinstance(on_confirm, IRBlock):
                    self._write(", confirmButton = { Button(onClick = {", inst)
                    self.indent_level += 1; self.visit_block(on_confirm); self.indent_level -= 1
                    self._write("}) { Text(\"OK\") } }")
                self._write(")")
                self.imports.add("androidx.compose.material3.AlertDialog")
            elif inst.func_name == "Snackbar":
                msg = self._v(inst.args[0]) if inst.args else "null"
                self._write(f"Snackbar({{ Text({msg}.toString()) }})", inst)
            elif inst.func_name == "ModalBottomSheet":
                on_dismiss = inst.keywords.get("on_dismiss", None)
                has_dismiss = isinstance(on_dismiss, IRBlock)
                self._write("ModalBottomSheet(onDismissRequest = {", inst)
                if has_dismiss:
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(on_dismiss); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}) {")
                if inst.body:
                    self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1
                self._write("}")
                self.imports.add("androidx.compose.material3.ModalBottomSheet")
            elif inst.func_name == "LazyColumn":
                items_val = next((self._v(v) for k, v in inst.keywords.items() if k == "items"), "emptyList<Any?>()")
                body_block = inst.keywords.get("body", None)
                self.imports.add("androidx.compose.foundation.lazy.LazyColumn")
                self.imports.add("androidx.compose.foundation.lazy.items")
                self._write(f"LazyColumn {{", inst)
                self.indent_level += 1
                self._write(f"items({items_val}) {{ item ->")
                if isinstance(body_block, IRBlock):
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(body_block); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}")
                self.indent_level -= 1; self._write("}")
            elif inst.func_name == "LazyRow":
                items_val = next((self._v(v) for k, v in inst.keywords.items() if k == "items"), "emptyList<Any?>()")
                body_block = inst.keywords.get("body", None)
                self.imports.add("androidx.compose.foundation.lazy.LazyRow")
                self.imports.add("androidx.compose.foundation.lazy.items")
                self._write(f"LazyRow {{", inst)
                self.indent_level += 1
                self._write(f"items({items_val}) {{ item ->")
                if isinstance(body_block, IRBlock):
                    self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                    self.visit_block(body_block); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}")
                self.indent_level -= 1; self._write("}")
            elif inst.func_name in {"TopAppBar", "BottomAppBar", "FloatingActionButton", "NavigationBar", "NavigationBarItem"}:
                if inst.func_name == "FloatingActionButton":
                    self._write("FloatingActionButton(", inst)
                else:
                    self._write(f"{camel_func}(", inst)
                inner = []
                for k, v in inst.keywords.items():
                    if isinstance(v, IRValue):
                        inner.append(f"{snake_to_camel(k)} = {self._v(v)}")
                self._write(", ".join(inner), inst)
                if inst.body:
                    self._write(") {", inst)
                    self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1; self._write("}")
                else:
                    self._write(")", inst)
            elif inst.body:
                self._write(f"{call} {{", inst)
                self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1; self._write("}")
            elif inst.func_name == "Text":
                self._write(f"Text({self._v(inst.args[0])}.toString())", inst)
            elif inst.func_name == "Spacer":
                self._write("Spacer(modifier = Modifier.weight(1f))", inst)
            elif inst.func_name == "Icon":
                icon_arg = self._v(inst.args[0]) if inst.args else "Icons.Default.Home"
                self._write(f"Icon(imageVector = {icon_arg}, contentDescription = null)", inst)
            else:
                self._write(call, inst)
        elif isinstance(inst, StateGet):
            obj = self._v(inst.state_var)
            if self.current_func_is_ui and not self.in_ui_lambda: self._write(f"val {self._v(inst.result)} = ({obj} as? StateFlow<Any?>)?.collectAsState()?.value ?: ({obj} as? MutableState<Any?>)?.value", inst)
            else: self._write(f"val {self._v(inst.result)} = ({obj} as? MutableStateFlow<Any?>)?.value ?: ({obj} as? MutableState<Any?>)?.value", inst)
        elif isinstance(inst, StateSet):
            obj = self._v(inst.state_var)
            self._write(f"({obj} as? MutableStateFlow<Any?>)?.value = {self._v(inst.new_value)}", inst)
            self._write(f"({obj} as? MutableState<Any?>)?.value = {self._v(inst.new_value)}", inst)
        elif isinstance(inst, Return):
            if inst.value: self._write(f"return {self._v(inst.value)}", inst)
            else: self._write("return", inst)
        elif isinstance(inst, TryExcept):
            self._write("try {", inst); self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1
            self._write(f"}} catch ({inst.exc_name or 'e'}: Exception) {{"); self.indent_level += 1; self.visit_block(inst.handler); self.indent_level -= 1; self._write("}")
        elif isinstance(inst, IRIf):
            self._write(f"if ({self._v(inst.condition)} as? Boolean ?: false) {{", inst); self.indent_level += 1; self.visit_block(inst.then_block); self.indent_level -= 1
            if inst.else_block: self._write("} else {"); self.indent_level += 1; self.visit_block(inst.else_block); self.indent_level -= 1
            self._write("}")
        elif isinstance(inst, NavigatorPush):
            screen_camel = snake_to_camel(inst.screen_func)
            nav_args = ", ".join(f"{snake_to_camel(k)} = {self._v(v)}" for k, v in inst.kwargs.items())
            self._write(f"navigatorPush(\"{screen_camel}\"{', ' + nav_args if nav_args else ''})", inst)
            self.imports.add("androidx.compose.runtime.remember")
        elif isinstance(inst, NavigatorPop):
            if inst.result:
                self._write(f"navigatorPop({self._v(inst.result)})", inst)
            else:
                self._write("navigatorPop()", inst)
        elif isinstance(inst, Raise): self._write(f"throw Exception(${self._v(inst.value)}.toString())", inst)
