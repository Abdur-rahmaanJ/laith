from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet
)
from laith.compiler.backend.kotlin.mapping import map_type_to_kotlin

class KotlinEmitter:
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.imports = {
            "laith.runtime.*",
            "kotlinx.coroutines.*",
            "androidx.compose.runtime.*"
        }

    def _indent(self):
        return "    " * self.indent_level

    def _write(self, text: str):
        self.output.append(f"{self._indent()}{text}")

    def emit(self, module: IRModule) -> str:
        # Collect imports from decorators
        for func in module.functions:
            for dec in func.decorators:
                if dec["name"] == "periodic_task":
                    self.imports.add("android.content.Context")
                    self.imports.add("androidx.work.WorkerParameters")
                if dec["name"] == "foreground_service":
                    self.imports.add("android.app.Notification")
                    self.imports.add("android.app.Service")
                    self.imports.add("android.content.Intent")

        header = [f"import {imp}" for imp in sorted(list(self.imports))]
        header.append("")
        
        for func in module.functions:
            self.visit_function(func)
            self.output.append("") # Spacer
            
        return "\n".join(header + self.output)

    def _v(self, val: IRValue) -> str:
        # If it's a numeric ID, prefix it, otherwise use as is (for parameters)
        # Actually, to be safe and consistent with SSA, we can always prefix or just use the ID
        # Let's prefix all IR values with 'v' to avoid collisions with Kotlin keywords
        return f"v_{val.id}"

    def visit_function(self, func: IRFunction):
        # Handle decorators (e.g., periodic_task -> WorkManager)
        for dec in func.decorators:
            if dec["name"] == "periodic_task":
                self._emit_worker(func, dec)
            if dec["name"] == "foreground_service":
                self._emit_service(func, dec)

        suspend = "suspend " if func.is_async else ""
        args_str = ", ".join(f"{self._v(arg)}: {map_type_to_kotlin(arg.type)}" for arg in func.args)
        ret_type = map_type_to_kotlin(func.return_type)
        
        self._write(f"{suspend}fun {func.name}({args_str}): {ret_type} {{")
        self.indent_level += 1
        
        for block in func.blocks:
            self.visit_block(block)
            
        self.indent_level -= 1
        self._write("}")

    def _emit_worker(self, func: IRFunction, decorator: dict):
        class_name = f"{func.name.capitalize()}Worker"
        self._write(f"class {class_name}(context: Context, params: WorkerParameters) : LaithWorker(context, params) {{")
        self.indent_level += 1
        self._write("override suspend fun executePython() {")
        self.indent_level += 1
        # Call the actual function. For simplicity we assume it takes no args for now if it's a periodic task
        self._write(f"{func.name}()")
        self.indent_level -= 1
        self._write("}")
        self.indent_level -= 1
        self._write("}")
        self.output.append("")

    def _emit_service(self, func: IRFunction, decorator: dict):
        class_name = f"{func.name.capitalize()}Service"
        self._write(f"class {class_name} : LaithService() {{")
        self.indent_level += 1
        
        self._write("override suspend fun executePython() {")
        self.indent_level += 1
        self._write(f"{func.name}()")
        self.indent_level -= 1
        self._write("}")
        
        self._write("override fun createNotification(): Notification {")
        self.indent_level += 1
        # Simplified notification creation for MVP
        self._write("// TODO: Use real notification builder based on decorator args")
        self._write("return Notification()") 
        self.indent_level -= 1
        self._write("}")
        
        self.indent_level -= 1
        self._write("}")
        self.output.append("")

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
            self._write(f"val {self._v(inst.result)} = {val}")
            
        elif isinstance(inst, BinaryOp):
            op_map = {
                "add": "+",
                "sub": "-",
                "mul": "*",
                "div": "/"
            }
            op = op_map.get(inst.op, inst.op)
            self._write(f"val {self._v(inst.result)} = {self._v(inst.left)} {op} {self._v(inst.right)}")
            
        elif isinstance(inst, Call):
            args_str = ", ".join(f"{self._v(arg)}" for arg in inst.args)
            if inst.result:
                self._write(f"val {self._v(inst.result)} = {inst.func_name}({args_str})")
            else:
                self._write(f"{inst.func_name}({args_str})")

        elif isinstance(inst, UICall):
            args_list = [f"{self._v(arg)}" for arg in inst.args]
            
            for key, val in inst.keywords.items():
                # Map Python snake_case to Kotlin camelCase for common Compose parameters
                kotlin_key = key.replace("_", "") if "_" in key else key
                # Special case for on_click -> onClick
                if key == "on_click":
                    kotlin_key = "onClick"
                
                if isinstance(val, IRBlock):
                    # It's a lambda block
                    args_list.append(f"{kotlin_key} = {{")
                    # We'll handle the block body separately if it's the last arg or just inline it
                    # For simplicity, we'll inline it here but it needs better formatting
                else:
                    args_list.append(f"{kotlin_key} = {self._v(val)}")
            
            args_str = ", ".join(args_list)
            
            # If there's a trailing lambda block among keywords, it's complex
            # For MVP: if it's a Button with on_click, we handle it specifically
            if inst.func_name == "Button" and "on_click" in inst.keywords:
                lambda_block = inst.keywords["on_click"]
                # Remove onClick from args_str to avoid duplication if handled specially
                # (Re-building args_str without onClick)
                other_args = [f"{self._v(arg)}" for arg in inst.args]
                args_str = ", ".join(other_args)
                
                self._write(f"Button(onClick = {{")
                self.indent_level += 1
                self.visit_block(lambda_block)
                self.indent_level -= 1
                self._write(f"}}) {{")
                self.indent_level += 1
                if inst.body:
                    self.visit_block(inst.body)
                self.indent_level -= 1
                self._write("}")
            elif inst.body:
                self._write(f"{inst.func_name}({args_str}) {{")
                self.indent_level += 1
                self.visit_block(inst.body)
                self.indent_level -= 1
                self._write("}")
            else:
                self._write(f"{inst.func_name}({args_str})")

        elif isinstance(inst, StateInit):
            self._write(f"val {self._v(inst.result)} = remember {{ mutableStateOf({self._v(inst.initial_value)}) }}")

        elif isinstance(inst, StateGet):
            self._write(f"val {self._v(inst.result)} = {self._v(inst.state_var)}.value")

        elif isinstance(inst, StateSet):
            self._write(f"{self._v(inst.state_var)}.value = {self._v(inst.new_value)}")
                
        elif isinstance(inst, Return):
            if inst.value:
                self._write(f"return {self._v(inst.value)}")
            else:
                self._write("return")
