import re
import os
from typing import Dict, List, Optional, Set, Tuple, Union
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop,
    IRClass, IRField, IRMethod, ClassInit, AttributeGet, AttributeSet, MethodCall,
    Jump, Branch, IRIf, TryExcept, Raise
)
from laith.compiler.backend.kotlin.mapping import map_type_to_kotlin

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
        # side-effects that need context but aren't UI
        self.needs_context: Set[str] = {"vibrate", "get_location", "request_location_permission"}
        self.imports = {
            "laith.runtime.*",
            "kotlinx.coroutines.*",
            "kotlinx.coroutines.flow.*",
            "androidx.compose.runtime.*",
            "androidx.compose.ui.platform.LocalContext",
            "androidx.compose.foundation.layout.*",
            "androidx.compose.material3.*",
            "androidx.compose.ui.Modifier"
        }

    def _indent(self): return "    " * self.indent_level
    def _write(self, text: str, inst: Optional[IRInstruction] = None):
        self.output.append(f"{self._indent()}{text}")
        if inst and inst.source_line: self.source_map.append((len(self.output), inst.source_line))

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
        self._emit_scheduler(module); self._emit_native_lib(module)
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
        if is_ui: self._write("@Composable")
        self._write(f"{'suspend ' if method.is_async else ''}fun {method.name}({', '.join(f'{self._v(a)}: {map_type_to_kotlin(a.type)}' for a in method.args[1:])}): {map_type_to_kotlin(method.return_type)} {{")
        self.indent_level += 1
        if len(method.args) > 0: self.current_self_id = method.args[0].id; self._write(f"val {self._v(method.args[0])} = this")
        prev_ui = self.current_func_is_ui; self.current_func_is_ui = is_ui
        if is_ui: self._write("val context = LocalContext.current")
        for block in method.blocks: self.visit_block(block)
        self.indent_level -= 1; self._write("}")
        self.current_func_is_ui = prev_ui; self.current_self_id = None

    def visit_function(self, func: IRFunction):
        is_ui = func.name in self.ui_functions
        if is_ui: self._write("@Composable")
        self._write(f"{'suspend ' if func.is_async else ''}fun {func.name}({', '.join(f'{self._v(a)}: {map_type_to_kotlin(a.type)}' for a in func.args)}): {map_type_to_kotlin(func.return_type)} {{")
        self.indent_level += 1
        prev_ui = self.current_func_is_ui; self.current_func_is_ui = is_ui
        if is_ui: self._write("val context = LocalContext.current")
        else: self._write("val context = laith.runtime.LaithContext.current")
        for block in func.blocks: self.visit_block(block)
        self.indent_level -= 1; self._write("}")
        self.current_func_is_ui = prev_ui

    def _emit_scheduler(self, module: IRModule):
        self._write("fun scheduleLaithTasks(context: android.content.Context) { laith.runtime.LaithContext.current = context }")
    def _emit_native_lib(self, module: IRModule): self._write("object NativeLib { init { System.loadLibrary(\"laith-native\") } }")

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
        if val.id.startswith("fun_ref_"): return val.id.replace("fun_ref_", "")
        if val.id == "context": return "context"
        if "." in val.type.name and val.id == val.type.name.split(".")[-1]: return val.type.name
        if val.id[0].isupper() and val.id not in ["AppState", "LabState", "Lab", "App", "self"]: return val.id
        return f"v_{val.id}"

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
                 cb = inst.args[0] if len(inst.args) > 0 and isinstance(inst.args[0], IRBlock) else None
                 if inst.func_name == "get_location": self._write("PythonRuntime.getLastLocation(context) { lat, lon ->", inst)
                 else: self._write("PythonRuntime.requestLocationPermission(context) { granted ->", inst)
                 if cb: self.indent_level += 1; self.visit_block(cb); self.indent_level -= 1
                 self._write("}"); return
            args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
            if inst.func_name == "vibrate": self._write(f"PythonRuntime.vibrate(context, ({args} as? Number)?.toLong() ?: 500L)", inst)
            elif inst.result: self._write(f"val {self._v(inst.result)} = {inst.func_name}({args})", inst)
            else: self._write(f"{inst.func_name}({args})", inst)
        elif isinstance(inst, MethodCall):
            args = ", ".join(self._v(a) if isinstance(a, IRValue) else "{}" for a in inst.args)
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            safe = not self.current_func_is_ui and inst.obj.id == "context"
            op = "?" if safe else ""
            if inst.method_name == "set":
                v = self._v(inst.args[0])
                self._write(f"({obj} as? MutableStateFlow<Any?>)?.value = {v}", inst)
                self._write(f"({obj} as? MutableState<Any?>)?.value = {v}", inst)
            elif inst.result: self._write(f"val {self._v(inst.result)} = {obj}{op}.{inst.method_name}({args})", inst)
            else: self._write(f"{obj}{op}.{inst.method_name}({args})", inst)
        elif isinstance(inst, ClassInit):
            args = ", ".join(self._v(a) for a in inst.args)
            if "." in inst.result.type.name: 
                 self._write(f"val {self._v(inst.result)} = {inst.result.type.name}({args})", inst)
            else: self._write(f"val {self._v(inst.result)} = {inst.class_name}().apply {{ __init__({args}) }}", inst)
        elif isinstance(inst, AttributeGet):
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            if "." in inst.obj.type.name: obj = inst.obj.type.name
            self._write(f"val {self._v(inst.result)} = {obj}.{inst.attr_name}", inst)
        elif isinstance(inst, AttributeSet):
            obj = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            self._write(f"{obj}.{inst.attr_name} = {self._v(inst.value)}", inst)
        elif isinstance(inst, StateInit):
            v = self._v(inst.initial_value)
            if self.current_func_is_ui: self._write(f"val {self._v(inst.result)} = remember {{ mutableStateOf<Any?>({v}) }}", inst)
            else: self._write(f"val {self._v(inst.result)} = MutableStateFlow<Any?>({v})", inst)
        elif isinstance(inst, UICall):
            args = []
            if inst.func_name == "Button" and inst.args: pass
            else: args = [self._v(a) for a in inst.args]
            for k, v in inst.keywords.items():
                if not isinstance(v, IRBlock): args.append(f"{k.replace('_', '') if k != 'on_click' else 'onClick'} = {self._v(v)}")
            call = f"{inst.func_name}({', '.join(args)})"
            has_click = any(isinstance(v, IRBlock) for v in inst.keywords.values())
            if inst.func_name == "Button" and has_click:
                self._write(f"Button(onClick = {{", inst)
                self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                self.visit_block(inst.keywords[next(k for k, v in inst.keywords.items() if isinstance(v, IRBlock))]); self.indent_level -= 1; self.in_ui_lambda = prev
                self._write("}) {"); self.indent_level += 1; self._write(f"Text({self._v(inst.args[0])}.toString())"); self.indent_level -= 1; self._write("}")
            elif inst.body:
                self._write(f"{call} {{", inst)
                self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1; self._write("}")
            else:
                 if inst.func_name == "Text": self._write(f"Text({self._v(inst.args[0])}.toString())", inst)
                 else: self._write(call, inst)
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
        elif isinstance(inst, Raise): self._write(f"throw Exception(${self._v(inst.value)}.toString())", inst)
