import ast
from typing import Dict, List, Optional, Union
from laith.compiler.frontend.symbols import Scope, Symbol, SymbolKind, Type, ANY_TYPE, VOID_TYPE
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop
)


class IRBuilder:
    def __init__(self, global_scope: Scope):
        self.global_scope = global_scope
        self.module = IRModule()
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBlock] = None
        self.value_counter = 0
        self.scope_values: List[Dict[str, IRValue]] = [{}]
        self.state_vars: List[set] = [set()] # Set of IDs that are state variables
        self.channels: List[set] = [set()] # Set of IDs that are channels

    def _next_id(self) -> str:
        id_ = str(self.value_counter)
        self.value_counter += 1
        return id_

    def _push_scope(self):
        self.scope_values.append({})
        self.state_vars.append(set())
        self.channels.append(set())

    def _pop_scope(self):
        self.scope_values.pop()
        self.state_vars.pop()
        self.channels.pop()

    def _set_value(self, name: str, value: IRValue, is_state: bool = False, is_channel: bool = False):
        self.scope_values[-1][name] = value
        if is_state:
            self.state_vars[-1].add(value.id)
        if is_channel:
            self.channels[-1].add(value.id)

    def _is_state(self, val: IRValue) -> bool:
        for s in reversed(self.state_vars):
            if val.id in s:
                return True
        return False

    def _is_channel(self, val: IRValue) -> bool:
        for c in reversed(self.channels):
            if val.id in c:
                return True
        return False

    def _get_value(self, name: str) -> Optional[IRValue]:
        for scope in reversed(self.scope_values):
            if name in scope:
                return scope[name]
        return None

    def build(self, tree: ast.AST):
        # Create a special function for global initializations
        global_init = IRFunction(
            name="global_init",
            return_type=VOID_TYPE,
            args=[]
        )
        self.module.functions.append(global_init)
        self.current_function = global_init
        self.current_block = IRBlock(label="init")
        global_init.blocks.append(self.current_block)

        for stmt in tree.body:
            self.visit(stmt)
            
        self.current_function = None
        self.current_block = None
        return self.module

    def visit(self, node: ast.AST):
        method = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST):
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

    def visit_Import(self, node: ast.Import):
        pass # Imports are handled by the compiler's built-in logic for now

    def visit_ImportFrom(self, node: ast.ImportFrom):
        pass

    def visit_JoinedStr(self, node: ast.JoinedStr) -> IRValue:
        # Lower f-string to a sequence of string additions
        if not node.values:
            return self.visit_expr(ast.Constant(value=""))
        
        res = self.visit_expr(node.values[0])
        for part in node.values[1:]:
            part_val = self.visit_expr(part)
            # SSA: create a new result for every addition
            new_res = IRValue(id=self._next_id(), type=STR_TYPE)
            inst = BinaryOp(result=new_res, op="add", left=res, right=part_val)
            self.current_block.add_instruction(inst)
            res = new_res
        return res

    def visit_FormattedValue(self, node: ast.FormattedValue) -> IRValue:
        # For now, just visit the value. 
        # Kotlin's '+' handles string conversion automatically.
        return self.visit_expr(node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self._visit_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self._visit_func(node, is_async=True)

    def _visit_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        # Find function symbol
        symbol = self.global_scope.lookup(node.name)
        
        # Find the function scope created during semantic analysis
        # In a real compiler, we might attach this to the node.
        # For now, we search in the children of the current scope.
        func_scope = next((s for s in self.global_scope.children if s.name == node.name), self.global_scope)
        
        args = []
        self._push_scope()
        for arg in node.args.args:
            # Look up parameter symbol in the function's scope
            arg_symbol = func_scope.lookup(arg.arg)
            arg_type = arg_symbol.type if arg_symbol else ANY_TYPE
            arg_val = IRValue(id=arg.arg, type=arg_type)
            args.append(arg_val)
            self._set_value(arg.arg, arg_val)

        func = IRFunction(
            name=node.name,
            return_type=symbol.type if symbol else VOID_TYPE,
            args=args,
            is_async=is_async,
            decorators=symbol.metadata.get("decorators", []) if symbol else []
        )
        self.current_function = func
        self.module.functions.append(func)
        
        # Initial block
        entry_block = IRBlock(label="entry")
        func.blocks.append(entry_block)
        self.current_block = entry_block
        
        for stmt in node.body:
            self.visit(stmt)
            
        self._pop_scope()
        self.current_function = None
        self.current_block = None

    def visit_Assign(self, node: ast.Assign):
        # Simplified: target = value
        value_ir = self.visit_expr(node.value)
        target = node.targets[0]
        if isinstance(target, ast.Name):
            # Check if it's a state or channel initialization
            is_state = False
            is_channel = False
            if self.current_block and self.current_block.instructions:
                last_inst = self.current_block.instructions[-1]
                if isinstance(last_inst, StateInit) and last_inst.result == value_ir:
                    is_state = True
                elif isinstance(last_inst, ChannelInit) and last_inst.result == value_ir:
                    is_channel = True
            
            self._set_value(target.id, value_ir, is_state=is_state, is_channel=is_channel)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        value_ir = self.visit_expr(node.value) if node.value else None
        if isinstance(node.target, ast.Name) and value_ir:
            is_state = False
            is_channel = False
            if self.current_block and self.current_block.instructions:
                last_inst = self.current_block.instructions[-1]
                if isinstance(last_inst, StateInit) and last_inst.result == value_ir:
                    is_state = True
                elif isinstance(last_inst, ChannelInit) and last_inst.result == value_ir:
                    is_channel = True
            self._set_value(node.target.id, value_ir, is_state=is_state, is_channel=is_channel)

    def visit_Return(self, node: ast.Return):
        value_ir = self.visit_expr(node.value) if node.value else None
        inst = Return(value=value_ir)
        self.current_block.add_instruction(inst)

    def visit_Expr(self, node: ast.Expr):
        self.visit_expr(node.value)

    def visit_expr(self, node: ast.AST) -> IRValue:
        if isinstance(node, ast.Constant):
            # We need a type for the constant
            from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE
            val_type = ANY_TYPE
            if isinstance(node.value, int): val_type = INT_TYPE
            elif isinstance(node.value, str): val_type = STR_TYPE
            elif isinstance(node.value, bool): val_type = BOOL_TYPE
            
            res_val = IRValue(id=self._next_id(), type=val_type)
            inst = Constant(result=res_val, value=node.value)
            self.current_block.add_instruction(inst)
            return res_val
            
        if isinstance(node, ast.Name):
            val = self._get_value(node.id)
            if val is None:
                raise Exception(f"Undefined variable {node.id}")
            return val
            
        if isinstance(node, ast.BinOp):
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.right)
            # Simplified op mapping
            op_map = {
                ast.Add: "add",
                ast.Sub: "sub",
                ast.Mult: "mul",
                ast.Div: "div"
            }
            op_name = op_map[type(node.op)]
            res_val = IRValue(id=self._next_id(), type=left.type) # Simplified type propagation
            inst = BinaryOp(result=res_val, op=op_name, left=left, right=right)
            self.current_block.add_instruction(inst)
            return res_val

        if isinstance(node, ast.Attribute):
            value_ir = self.visit_expr(node.value)
            if self._is_state(value_ir) and node.attr == "value":
                res_val = IRValue(id=self._next_id(), type=ANY_TYPE)
                inst = StateGet(result=res_val, state_var=value_ir)
                self.current_block.add_instruction(inst)
                return res_val

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                
                if func_name == "state":
                    init_val = self.visit_expr(node.args[0])
                    res_val = IRValue(id=self._next_id(), type=ANY_TYPE)
                    inst = StateInit(result=res_val, initial_value=init_val)
                    self.current_block.add_instruction(inst)
                    return res_val

                if func_name == "Channel":
                    res_val = IRValue(id=self._next_id(), type=ANY_TYPE)
                    inst = ChannelInit(result=res_val)
                    self.current_block.add_instruction(inst)
                    return res_val

                if func_name == "start_service":
                    target_func = node.args[0].id
                    inst = ServiceStart(func_name=target_func)
                    self.current_block.add_instruction(inst)
                    return IRValue(id="void", type=VOID_TYPE)

                if func_name == "stop_service":
                    target_func = node.args[0].id
                    inst = ServiceStop(func_name=target_func)
                    self.current_block.add_instruction(inst)
                    return IRValue(id="void", type=VOID_TYPE)

                # Check if it's a UI component
                ui_components = {"Column", "Row", "Box", "Text", "Button"}
                if func_name in ui_components:
                    children = []
                    immediate_args = []
                    for arg in node.args:
                        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id in ui_components:
                            children.append(arg)
                        else:
                            immediate_args.append(arg)
                    
                    keywords = {}
                    for kw in node.keywords:
                        if isinstance(kw.value, ast.Lambda):
                            self._push_scope()
                            # Bind lambda args if any
                            for arg in kw.value.args.args:
                                arg_val = IRValue(id=arg.arg, type=ANY_TYPE)
                                self._set_value(arg.arg, arg_val)

                            parent_block = self.current_block
                            lambda_block = IRBlock(label=f"{func_name}_{kw.arg}")
                            self.current_block = lambda_block
                            self.visit_expr(kw.value.body)
                            self.current_block = parent_block
                            self._pop_scope()
                            keywords[kw.arg] = lambda_block
                        else:
                            keywords[kw.arg] = self.visit_expr(kw.value)

                    args = [self.visit_expr(arg) for arg in immediate_args]
                    
                    ui_body = None
                    if children:
                        parent_block = self.current_block
                        ui_body = IRBlock(label=f"{func_name}_body")
                        self.current_block = ui_body
                        for child in children:
                            self.visit_expr(child)
                        self.current_block = parent_block
                    
                    inst = UICall(func_name=func_name, args=args, body=ui_body, keywords=keywords)
                    self.current_block.add_instruction(inst)
                    return IRValue(id="void", type=VOID_TYPE)
                
                args = [self.visit_expr(arg) for arg in node.args]
                # Check for built-ins or defined functions
                res_val = IRValue(id=self._next_id(), type=ANY_TYPE)
                inst = Call(result=res_val, func_name=func_name, args=args)
                self.current_block.add_instruction(inst)
                return res_val
                
            if isinstance(node.func, ast.Attribute):
                obj = self.visit_expr(node.func.value)
                if self._is_state(obj) and node.func.attr == "set":
                    new_val = self.visit_expr(node.args[0])
                    inst = StateSet(state_var=obj, new_value=new_val)
                    self.current_block.add_instruction(inst)
                    return IRValue(id="void", type=VOID_TYPE)
                
                if self._is_channel(obj):
                    if node.func.attr == "publish":
                        val = self.visit_expr(node.args[0])
                        inst = ChannelSend(channel=obj, value=val)
                        self.current_block.add_instruction(inst)
                        return IRValue(id="void", type=VOID_TYPE)
                    
                    if node.func.attr == "collect":
                        # Assume collect takes a lambda for what to do with the value
                        if isinstance(node.args[0], ast.Lambda):
                            l = node.args[0]
                            self._push_scope()
                            # Bind lambda args
                            for arg in l.args.args:
                                arg_val = IRValue(id=arg.arg, type=ANY_TYPE)
                                self._set_value(arg.arg, arg_val)

                            parent_block = self.current_block
                            collect_block = IRBlock(label="collect_body")
                            self.current_block = collect_block
                            self.visit_expr(l.body)
                            self.current_block = parent_block
                            self._pop_scope()
                            inst = ChannelCollect(channel=obj, body=collect_block)
                            self.current_block.add_instruction(inst)
                            return IRValue(id="void", type=VOID_TYPE)
        
        raise NotImplementedError(f"No visitor for expr {node.__class__.__name__}")
