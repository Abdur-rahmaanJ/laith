from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, IRClass, IRField, IRMethod
)
from typing import List, Dict, Any, Union

class CPPEmitter:
    def __init__(self):
        self.output = []
        self.indent_level = 0

    def _indent(self):
        return "    " * self.indent_level

    def _write(self, text: str):
        self.output.append(f"{self._indent()}{text}")

    def emit(self, module: IRModule) -> str:
        # Collect native functions and native methods
        native_functions = [f for f in module.functions if any(d["name"] == "native" for d in f.decorators)]
        native_methods = []
        for cls in module.classes:
            for method in cls.methods:
                if any(d["name"] == "native" for d in method.decorators):
                    native_methods.append((cls.name, method))
        
        if not native_functions and not native_methods:
            return ""

        header = [
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            "#include <cstdint>",
            "",
            "extern \"C\" {"
        ]
        self.output = []
        self.indent_level = 1
        
        for func in native_functions:
            self.visit_function(func)
            self.output.append("")

        for cls_name, method in native_methods:
            # For C linkage, mangled name: ClassName_methodName
            mangled_name = f"{cls_name}_{method.name}"
            # Create a clone for visitation to avoid mutating original IR
            mangled_method = IRMethod(
                name=mangled_name,
                return_type=method.return_type,
                args=method.args,
                is_async=method.is_async,
                blocks=method.blocks,
                decorators=method.decorators
            )
            self.visit_function(mangled_method)
            self.output.append("")

        self.indent_level = 0
        footer = ["}", ""]
        
        return "\n".join(header + self.output + footer)

    def _v(self, val: IRValue) -> str:
        return f"v_{val.id}"

    def _map_type(self, t) -> str:
        from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE
        if t == INT_TYPE: return "int64_t"
        if t == STR_TYPE: return "const char*"
        if t == BOOL_TYPE: return "bool"
        return "void*"

    def visit_function(self, func: Union[IRFunction, IRMethod]):
        ret_type = self._map_type(func.return_type)
        args_str = ", ".join(f"{self._map_type(arg.type)} {self._v(arg)}" for arg in func.args)
        
        self._write(f"{ret_type} {func.name}({args_str}) {{")
        self.indent_level += 1
        
        for block in func.blocks:
            self.visit_block(block)
            
        self.indent_level -= 1
        self._write("}")

    def visit_block(self, block: IRBlock):
        for inst in block.instructions:
            self.visit_instruction(inst)

    def visit_instruction(self, inst: IRInstruction):
        if isinstance(inst, Constant):
            val = inst.value
            if isinstance(val, str):
                val = f'"{val}"'
            elif isinstance(val, bool):
                val = str(val).lower()
            self._write(f"{self._map_type(inst.result.type)} {self._v(inst.result)} = {val};")
            
        elif isinstance(inst, BinaryOp):
            op_map = {"add": "+", "sub": "-", "mul": "*", "div": "/", "lt": "<", "gt": ">"}
            op = op_map.get(inst.op, inst.op)
            self._write(f"{self._map_type(inst.result.type)} {self._v(inst.result)} = {self._v(inst.left)} {op} {self._v(inst.right)};")
            
        elif isinstance(inst, Call):
            args_str = ", ".join(f"{self._v(arg)}" for arg in inst.args)
            if inst.result:
                self._write(f"{self._map_type(inst.result.type)} {self._v(inst.result)} = {inst.func_name}({args_str});")
            else:
                self._write(f"{inst.func_name}({args_str});")

        elif isinstance(inst, Return):
            if inst.value:
                self._write(f"return {self._v(inst.value)};")
            else:
                self._write("return;")
