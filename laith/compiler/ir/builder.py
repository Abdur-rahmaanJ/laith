import ast
from typing import Dict, List, Optional, Union
from laith.compiler.frontend.symbols import Scope, Symbol, SymbolKind, Type, ANY_TYPE, VOID_TYPE
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRValue, IRInstruction,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet
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

    def _next_id(self) -> str:
        id_ = str(self.value_counter)
        self.value_counter += 1
        return id_

    def _push_scope(self):
        self.scope_values.append({})
        self.state_vars.append(set())

    def _pop_scope(self):
        self.scope_values.pop()
        self.state_vars.pop()

    def _set_value(self, name: str, value: IRValue, is_state: bool = False):
        self.scope_values[-1][name] = value
        if is_state:
            self.state_vars[-1].add(value.id)

    def _is_state(self, val: IRValue) -> bool:
        for s in reversed(self.state_vars):
            if val.id in s:
                return True
        return False

    def _get_value(self, name: str) -> Optional[IRValue]:
        for scope in reversed(self.scope_values):
            if name in scope:
                return scope[name]
        return None

    def build(self, tree: ast.AST):
        for stmt in tree.body:
            self.visit(stmt)
        return self.module

    def visit(self, node: ast.AST):
        method = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST):
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

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
            return_type=symbol.type if symbol else ANY_TYPE,
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
            # Check if the expression that produced value_ir was a state() call
            # This is a bit hacky, but for MVP we can check the last instruction if it's StateInit
            is_state = False
            if self.current_block and self.current_block.instructions:
                last_inst = self.current_block.instructions[-1]
                if isinstance(last_inst, StateInit) and last_inst.result == value_ir:
                    is_state = True
            
            self._set_value(target.id, value_ir, is_state=is_state)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        value_ir = self.visit_expr(node.value) if node.value else None
        if isinstance(node.target, ast.Name) and value_ir:
            is_state = False
            if self.current_block and self.current_block.instructions:
                last_inst = self.current_block.instructions[-1]
                if isinstance(last_inst, StateInit) and last_inst.result == value_ir:
                    is_state = True
            self._set_value(node.target.id, value_ir, is_state=is_state)

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
                            parent_block = self.current_block
                            lambda_block = IRBlock(label=f"{func_name}_{kw.arg}")
                            self.current_block = lambda_block
                            self.visit_expr(kw.value.body)
                            self.current_block = parent_block
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
        
        raise NotImplementedError(f"No visitor for expr {node.__class__.__name__}")
