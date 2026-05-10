import re
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop
)
from laith.compiler.backend.kotlin.mapping import map_type_to_kotlin

class KotlinEmitter:
    def __init__(self):
        self.output = []
        self.indent_level = 0
        self.global_values = set()
        self.current_func_is_ui = False
        self.imports = {
            "laith.runtime.*",
            "kotlinx.coroutines.*",
            "kotlinx.coroutines.flow.*",
            "androidx.compose.runtime.*",
            "androidx.compose.ui.platform.LocalContext"
        }

    def _indent(self):
        return "    " * self.indent_level

    def _write(self, text: str):
        self.output.append(f"{self._indent()}{text}")

    def emit(self, module: IRModule) -> str:
        # Collect native function names for call routing
        self.native_func_names = {f.name for f in module.functions if any(d["name"] == "native" for d in f.decorators)}

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

        # Handle global initializations as top-level properties
        global_init_func = next((f for f in module.functions if f.name == "global_init"), None)
        if global_init_func:
            for block in global_init_func.blocks:
                for inst in block.instructions:
                    if inst.result:
                        self.global_values.add(inst.result.id)
                    self.visit_top_level_instruction(inst)
            self.output.append("")

        for func in module.functions:
            if func.name == "global_init":
                continue
            self.visit_function(func)
            self.output.append("") # Spacer
            
        self._emit_scheduler(module)
        self._emit_native_lib(module)

        header = [f"import {imp}" for imp in sorted(list(self.imports))]
        header.append("")
        
        return "\n".join(header + self.output)

    def _emit_native_lib(self, module: IRModule):
        native_functions = [f for f in module.functions if any(d["name"] == "native" for d in f.decorators)]
        if not native_functions:
            return

        self._write("object NativeLib {")
        self.indent_level += 1
        self._write("init {")
        self.indent_level += 1
        self._write('System.loadLibrary("laith-native")')
        self.indent_level -= 1
        self._write("}")
        self.output.append("")

        for func in native_functions:
            args_str = ", ".join(f"{arg.id}: {map_type_to_kotlin(arg.type)}" for arg in func.args)
            ret_type = map_type_to_kotlin(func.return_type)
            self._write(f"external fun {func.name}({args_str}): {ret_type}")

        self.indent_level -= 1
        self._write("}")
        self.output.append("")

    def _emit_scheduler(self, module: IRModule):
        periodic_tasks = []
        for func in module.functions:
            for dec in func.decorators:
                if dec["name"] == "periodic_task":
                    periodic_tasks.append((func, dec))
        
        # Always emit the function, even if empty, to satisfy MainActivity call
        self.imports.add("android.content.Context")
        self._write("fun scheduleLaithTasks(context: Context) {")
        self.indent_level += 1
        
        if periodic_tasks:
            self.imports.add("androidx.work.PeriodicWorkRequestBuilder")
            self.imports.add("androidx.work.WorkManager")
            self.imports.add("androidx.work.ExistingPeriodicWorkPolicy")
            self.imports.add("java.util.concurrent.TimeUnit")
            self.imports.add("androidx.work.Constraints")
            self.imports.add("androidx.work.NetworkType")

            for func, dec in periodic_tasks:
                interval_str = dec["args"].get("interval", "15m")
                val, unit = self._parse_interval(interval_str)
                
                worker_name = f"{func.name.capitalize()}Worker"
                
                # Handle constraints
                self._write(f"val constraints_{func.name} = Constraints.Builder()")
                self.indent_level += 1
                if dec["args"].get("requires_wifi"):
                    self._write(".setRequiredNetworkType(NetworkType.UNMETERED)")
                if dec["args"].get("requires_charging"):
                    self._write(".setRequiresCharging(true)")
                self._write(".build()")
                self.indent_level -= 1
                
                self._write(f"val workRequest_{func.name} = PeriodicWorkRequestBuilder<{worker_name}>({val}, {unit})")
                self.indent_level += 1
                self._write(f".setConstraints(constraints_{func.name})")
                self._write(".build()")
                self.indent_level -= 1
                
                self._write(f'WorkManager.getInstance(context).enqueueUniquePeriodicWork("{func.name}", ExistingPeriodicWorkPolicy.KEEP, workRequest_{func.name})')

        self.indent_level -= 1
        self._write("}")
        self.output.append("")

    def _parse_interval(self, interval_str: str):
        match = re.match(r"(\d+)([smh])", interval_str)
        if not match:
            return 15, "TimeUnit.MINUTES"
        
        val, unit = match.groups()
        unit_map = {
            "s": "TimeUnit.SECONDS",
            "m": "TimeUnit.MINUTES",
            "h": "TimeUnit.HOURS"
        }
        return val, unit_map.get(unit, "TimeUnit.MINUTES")

    def visit_top_level_instruction(self, inst: IRInstruction):
        # Top-level instructions become properties
        if isinstance(inst, ChannelInit):
            self._write(f"val {self._v(inst.result)} = MutableSharedFlow<Any>()")
        elif isinstance(inst, StateInit):
            self._write(f"val {self._v(inst.result)} = MutableStateFlow({self._v(inst.initial_value)})")
            self.imports.add("kotlinx.coroutines.flow.MutableStateFlow")
        elif isinstance(inst, Constant):
            val = inst.value
            if isinstance(val, str): val = f'"{val}"'
            elif isinstance(val, bool): val = str(val).lower()
            self._write(f"val {self._v(inst.result)} = {val}")

    def _v(self, val: IRValue) -> str:
        return f"v_{val.id}"

    def visit_function(self, func: IRFunction):
        # Handle decorators (e.g., periodic_task -> WorkManager)
        for dec in func.decorators:
            if dec["name"] == "periodic_task":
                self._emit_worker(func, dec)
            if dec["name"] == "foreground_service":
                self._emit_service(func, dec)

        # Check if it's a UI function (contains UICall)
        has_ui = False
        for block in func.blocks:
            if any(isinstance(i, UICall) for i in block.instructions):
                has_ui = True
                break
        
        self.current_func_is_ui = has_ui
        if has_ui:
            self._write("@Composable")

        suspend = "suspend " if func.is_async else ""
        args_str = ", ".join(f"{self._v(arg)}: {map_type_to_kotlin(arg.type)}" for arg in func.args)
        ret_type = map_type_to_kotlin(func.return_type)
        
        self._write(f"{suspend}fun {func.name}({args_str}): {ret_type} {{")
        self.indent_level += 1
        
        if has_ui:
            self._write("val context = LocalContext.current")

        for block in func.blocks:
            self.visit_block(block)
            
        self.indent_level -= 1
        self._write("}")
        self.current_func_is_ui = False

    def _emit_worker(self, func: IRFunction, decorator: dict):
        class_name = f"{func.name.capitalize()}Worker"
        self._write(f"class {class_name}(context: Context, params: WorkerParameters) : LaithWorker(context, params) {{")
        self.indent_level += 1
        self._write("override suspend fun executePython() {")
        self.indent_level += 1
        self._write(f"{func.name}()")
        self.indent_level -= 1
        self._write("}")
        self.indent_level -= 1
        self._write("}")
        self.output.append("")

    def _emit_service(self, func: IRFunction, decorator: dict):
        class_name = f"{func.name.capitalize()}Service"
        self.imports.add("androidx.core.app.NotificationCompat")
        self.imports.add("android.app.NotificationChannel")
        self.imports.add("android.app.NotificationManager")
        self.imports.add("android.os.Build")

        self._write(f"class {class_name} : LaithService() {{")
        self.indent_level += 1
        
        self._write("override suspend fun executePython() {")
        self.indent_level += 1
        self._write(f"{func.name}()")
        self.indent_level -= 1
        self._write("}")
        
        self._write("override fun createNotification(): Notification {")
        self.indent_level += 1
        
        notification_text = decorator["args"].get("notification", "Laith Background Service")
        self._write(f'val channelId = "{func.name}_channel"')
        self._write('if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {')
        self.indent_level += 1
        self._write(f'val name = "{func.name} Service"')
        self._write('val importance = NotificationManager.IMPORTANCE_LOW')
        self._write('val channel = NotificationChannel(channelId, name, importance)')
        self._write('val notificationManager = getSystemService(NotificationManager::class.java)')
        self._write('notificationManager.createNotificationChannel(channel)')
        self.indent_level -= 1
        self._write('}')
        
        self._write('return NotificationCompat.Builder(this, channelId)')
        self.indent_level += 1
        self._write('.setContentTitle("Laith App")')
        self._write(f'.setContentText("{notification_text}")')
        self._write('.setSmallIcon(android.R.drawable.ic_menu_info_details)')
        self._write('.build()')
        self.indent_level -= 1
        
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
            
            # Check if calling a native function
            # Note: We should ideally have access to the full module or a symbol table here
            # For now, we assume if we're in KotlinEmitter and it's @native, we call via NativeLib
            # A more robust way would be to check a set of native_func_names
            prefix = ""
            if hasattr(self, 'native_func_names') and inst.func_name in self.native_func_names:
                prefix = "NativeLib."

            if inst.result:
                self._write(f"val {self._v(inst.result)} = {prefix}{inst.func_name}({args_str})")
            else:
                self._write(f"{prefix}{inst.func_name}({args_str})")

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
                
                # If there are non-keyword args, they might be labels
                for arg in inst.args:
                    # For MVP, assume string args are labels
                    self._write(f"Text({self._v(arg)})")

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
            if self.current_func_is_ui and inst.state_var.id in self.global_values:
                self._write(f"val {self._v(inst.result)} = {self._v(inst.state_var)}.collectAsState().value")
            else:
                self._write(f"val {self._v(inst.result)} = {self._v(inst.state_var)}.value")

        elif isinstance(inst, StateSet):
            self._write(f"{self._v(inst.state_var)}.value = {self._v(inst.new_value)}")

        elif isinstance(inst, ChannelInit):
            self._write(f"val {self._v(inst.result)} = MutableSharedFlow<Any>()")

        elif isinstance(inst, ChannelSend):
            # Using emit in a coroutine
            self._write(f"CoroutineScope(Dispatchers.Default).launch {{ {self._v(inst.channel)}.emit({self._v(inst.value)}) }}")

        elif isinstance(inst, ChannelCollect):
            # For now, we assume the lambda has exactly one argument
            # We need to find the name of that argument from the IR if possible, 
            # or just use a default like 'it' or 'v_data'
            # Let's try to infer from the first instruction in the block if it's a use
            self._write(f"CoroutineScope(Dispatchers.Main).launch {{")
            self.indent_level += 1
            # In a real compiler, the parameter name would be part of ChannelCollect
            self._write(f"{self._v(inst.channel)}.collect {{ v_data -> ")
            self.indent_level += 1
            self.visit_block(inst.body)
            self.indent_level -= 1
            self._write("}")
            self.indent_level -= 1
            self._write("}")

        elif isinstance(inst, ServiceStart):
            service_class = f"{inst.func_name.capitalize()}Service"
            self._write(f"val intent_{inst.func_name} = Intent(context, {service_class}::class.java)")
            self._write(f"if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{")
            self.indent_level += 1
            self._write(f"context.startForegroundService(intent_{inst.func_name})")
            self.indent_level -= 1
            self._write(f"}} else {{")
            self.indent_level += 1
            self._write(f"context.startService(intent_{inst.func_name})")
            self.indent_level -= 1
            self._write(f"}}")

        elif isinstance(inst, ServiceStop):
            service_class = f"{inst.func_name.capitalize()}Service"
            self._write(f"val intent_{inst.func_name} = Intent(context, {service_class}::class.java)")
            self._write(f"context.stopService(intent_{inst.func_name})")
                
        elif isinstance(inst, Return):
            if inst.value:
                self._write(f"return {self._v(inst.value)}")
            else:
                self._write("return")
