import re
import os
from typing import Dict, List, Optional, Set, Tuple
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop,
    IRClass, IRField, IRMethod, ClassInit, AttributeGet, AttributeSet, MethodCall,
    Jump, Branch
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
        self.source_map: List[Tuple[int, int]] = [] # (output_line, input_line)
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
        line_content = f"{self._indent()}{text}"
        self.output.append(line_content)
        if inst and inst.source_line:
             # Store mapping: current output line index (1-based) -> input source line
             self.source_map.append((len(self.output), inst.source_line))

    def emit(self, module: IRModule) -> str:
        self.native_func_names = {f.name for f in module.functions if any(d["name"] == "native" for d in f.decorators)}
        for cls in module.classes:
            for method in cls.methods:
                if any(d["name"] == "native" for d in method.decorators): self.native_func_names.add(method.name)

        # Handle global initializations
        global_init_func = next((f for f in module.functions if f.name == "global_init"), None)
        if global_init_func:
            for block in global_init_func.blocks:
                for inst in block.instructions:
                    if inst.result: self.global_values.add(inst.result.id)
                    self.visit_top_level_instruction(inst)
            self.output.append("")

        for cls in module.classes:
            self.visit_class(cls)
            self.output.append("")

        for func in module.functions:
            if func.name == "global_init": continue
            self.visit_function(func)
            self.output.append("")
            
        self._emit_scheduler(module)
        self._emit_native_lib(module)

        header = [f"import {imp}" for imp in sorted(list(self.imports))]
        header.append("")
        
        # Offset source map by header length
        header_len = len(header)
        final_map = [(out_l + header_len, in_l) for out_l, in_l in self.source_map]
        self.final_source_map = final_map

        return "\n".join(header + self.output)

    def get_source_map(self) -> List[Tuple[int, int]]:
        return self.final_source_map

    def visit_class(self, cls: IRClass):
        self.current_class_name = cls.name
        self._write(f"class {cls.name} {{")
        self.indent_level += 1
        for field in cls.fields: self._write(f"var {field.name}: Any? = null")
        for method in cls.methods: self.visit_method(method)
        self.indent_level -= 1
        self._write("}")
        self.current_class_name = None

    def visit_method(self, method: IRMethod):
        has_ui = False
        for block in method.blocks:
            if any(isinstance(i, UICall) for i in block.instructions): has_ui = True; break
        self.current_func_is_ui = has_ui
        if has_ui: self._write("@Composable")
        suspend = "suspend " if method.is_async else ""
        args_to_emit = method.args[1:] if len(method.args) > 0 else method.args
        args_str = ", ".join(f"{self._v(arg)}: {map_type_to_kotlin(arg.type)}" for arg in args_to_emit)
        ret_type = map_type_to_kotlin(method.return_type)
        self._write(f"{suspend}fun {method.name}({args_str}): {ret_type} {{")
        self.indent_level += 1
        if len(method.args) > 0:
            self.current_self_id = method.args[0].id
            self._write(f"val {self._v(method.args[0])} = this")
        for block in method.blocks: self.visit_block(block)
        self.indent_level -= 1
        self._write("}")
        self.current_func_is_ui = False
        self.current_self_id = None

    def visit_function(self, func: IRFunction):
        has_ui = False
        for block in func.blocks:
            if any(isinstance(i, UICall) for i in block.instructions): has_ui = True; break
        self.current_func_is_ui = has_ui
        if has_ui: self._write("@Composable")
        suspend = "suspend " if func.is_async else ""
        args_str = ", ".join(f"{self._v(arg)}: {map_type_to_kotlin(arg.type)}" for arg in func.args)
        ret_type = map_type_to_kotlin(func.return_type)
        self._write(f"{suspend}fun {func.name}({args_str}): {ret_type} {{")
        self.indent_level += 1
        if has_ui: self._write("val context = LocalContext.current")
        for block in func.blocks: self.visit_block(block)
        self.indent_level -= 1
        self._write("}")
        self.current_func_is_ui = False

    def _emit_native_lib(self, module: IRModule):
        self._write("object NativeLib { init { System.loadLibrary(\"laith-native\") } }")

    def _emit_scheduler(self, module: IRModule):
        self._write("fun scheduleLaithTasks(context: android.content.Context) { }")

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
            val = self._v(inst.initial_value)
            self._write(f"val {self._v(inst.result)} = MutableStateFlow<Any?>({val})", inst)
            self.imports.add("kotlinx.coroutines.flow.MutableStateFlow")

    def _v(self, val: IRValue) -> str:
        if "." in val.type.name and val.id == val.type.name.split(".")[-1]: return val.type.name
        if val.id[0].isupper() and val.id not in ["AppState", "LabState", "Lab", "App", "self"]: return val.id
        return f"v_{val.id}"

    def visit_block(self, block: IRBlock):
        for inst in block.instructions: self.visit_instruction(inst)

    def visit_instruction(self, inst: IRInstruction):
        if isinstance(inst, Constant):
            val = inst.value
            if isinstance(val, str): val = f'"{val}"'
            elif isinstance(val, bool): val = str(val).lower()
            self._write(f"val {self._v(inst.result)} = {val}", inst)
        elif isinstance(inst, BinaryOp):
            op_map = {"add": "+", "sub": "-", "mul": "*", "div": "/", "lt": "<", "gt": ">"}
            op = op_map.get(inst.op, inst.op)
            l_val, r_val = self._v(inst.left), self._v(inst.right)
            if inst.op == "add": 
                self._write(f"val {self._v(inst.result)} = \"${{({l_val} ?: \"\")}} ${{({r_val} ?: \"\")}} \".trim()", inst)
            else:
                l_expr = f"({l_val} as? Number)?.toInt() ?: 0"
                r_expr = f"({r_val} as? Number)?.toInt() ?: 0"
                self._write(f"val {self._v(inst.result)} = {l_expr} {op} {r_expr}", inst)
        elif isinstance(inst, Call):
            args_str = ", ".join(f"{self._v(arg)}" for arg in inst.args)
            if inst.result: self._write(f"val {self._v(inst.result)} = {inst.func_name}({args_str})", inst)
            else: self._write(f"{inst.func_name}({args_str})", inst)
        elif isinstance(inst, MethodCall):
            args_str = ", ".join(f"{self._v(arg)}" for arg in inst.args)
            obj_name = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            if inst.method_name == "set":
                v = self._v(inst.args[0])
                self._write(f"({obj_name} as? MutableStateFlow<Any?>)?.value = {v}", inst)
                self._write(f"({obj_name} as? MutableState<Any?>)?.value = {v}", inst)
                return
            if inst.result: self._write(f"val {self._v(inst.result)} = {obj_name}.{inst.method_name}({args_str})", inst)
            else: self._write(f"{obj_name}.{method_name}({args_str})", inst)
        elif isinstance(inst, ClassInit):
            args = ", ".join(self._v(a) for a in inst.args)
            fqn = inst.result.type.name
            if "." in fqn:
                ctx = "context" if self.current_func_is_ui else "null"
                self._write(f"val {self._v(inst.result)} = {fqn}({', '.join(filter(None, [ctx, args]))})", inst)
            else:
                self._write(f"val {self._v(inst.result)} = {inst.class_name}().apply {{ __init__({args}) }}", inst)
        elif isinstance(inst, AttributeGet):
            obj_name = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            if "." in inst.obj.type.name: obj_name = inst.obj.type.name
            self._write(f"val {self._v(inst.result)} = {obj_name}.{inst.attr_name}", inst)
        elif isinstance(inst, AttributeSet):
            obj_name = "this" if (self.current_self_id and inst.obj.id == self.current_self_id) else self._v(inst.obj)
            self._write(f"{obj_name}.{inst.attr_name} = {self._v(inst.value)}", inst)
        elif isinstance(inst, StateInit):
            val = self._v(inst.initial_value)
            if self.current_func_is_ui: self._write(f"val {self._v(inst.result)} = remember {{ mutableStateOf<Any?>({val}) }}", inst)
            else: self._write(f"val {self._v(inst.result)} = MutableStateFlow<Any?>({val})", inst)
        elif isinstance(inst, UICall):
            args_list = []
            if inst.func_name == "Button" and inst.args: label = self._v(inst.args[0])
            else: args_list = [self._v(a) for a in inst.args]
            for k, v in inst.keywords.items():
                if not isinstance(v, IRBlock):
                    kotlin_k = k.replace("_", "") if k != "on_click" else "onClick"
                    args_list.append(f"{kotlin_k} = {self._v(v)}")
            call_str = f"{inst.func_name}({', '.join(args_list)})"
            has_body = inst.body is not None
            has_click = any(isinstance(v, IRBlock) for v in inst.keywords.values())
            if inst.func_name == "Button" and has_click:
                kw_name = next(k for k, v in inst.keywords.items() if isinstance(v, IRBlock))
                block = inst.keywords[kw_name]
                self._write(f"Button(onClick = {{", inst)
                self.indent_level += 1; prev = self.in_ui_lambda; self.in_ui_lambda = True
                self.visit_block(block); self.in_ui_lambda = prev; self.indent_level -= 1
                self._write("}) {")
                self.indent_level += 1; self._write(f"Text({self._v(inst.args[0])})")
                self.indent_level -= 1; self._write("}")
            elif has_body:
                self._write(f"{inst.func_name}({', '.join(args_list)}) {{", inst)
                self.indent_level += 1; self.visit_block(inst.body); self.indent_level -= 1
                self._write("}")
            else: self._write(call_str, inst)
        elif isinstance(inst, StateGet):
            obj_name = self._v(inst.state_var)
            if self.current_func_is_ui and not self.in_ui_lambda:
                self._write(f"val {self._v(inst.result)} = ({obj_name} as? StateFlow<Any?>)?.collectAsState()?.value ?: ({obj_name} as? MutableState<Any?>)?.value", inst)
            else:
                self._write(f"val {self._v(inst.result)} = ({obj_name} as? MutableStateFlow<Any?>)?.value ?: ({obj_name} as? MutableState<Any?>)?.value", inst)
        elif isinstance(inst, StateSet):
            obj_name = self._v(inst.state_var)
            self._write(f"({obj_name} as? MutableStateFlow<Any?>)?.value = {self._v(inst.new_value)}", inst)
            self._write(f"({obj_name} as? MutableState<Any?>)?.value = {self._v(inst.new_value)}", inst)
        elif isinstance(inst, Return):
            if inst.value: self._write(f"return {self._v(inst.value)}", inst)
            else: self._write("return", inst)
        elif isinstance(inst, TryExcept):
            self._write("try {", inst)
            self.indent_level += 1
            self.visit_block(inst.body)
            self.indent_level -= 1
            exc_var = inst.exc_name or "e"
            self._write(f"}} catch ({exc_var}: Exception) {{")
            self.indent_level += 1
            self.visit_block(inst.handler)
            self.indent_level -= 1
            self._write("}")
        elif isinstance(inst, Raise):
            # In Phase 12 we'll wrap the raised value in an Exception if it's not one
            self._write(f"throw Exception(${self._v(inst.value)}.toString())", inst)
