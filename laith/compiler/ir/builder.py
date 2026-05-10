import ast
from typing import Dict, List, Optional, Union
from laith.compiler.frontend.symbols import Scope, Symbol, SymbolKind, Type, ANY_TYPE, VOID_TYPE, STR_TYPE, BOOL_TYPE, INT_TYPE
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction, IRValue,
    Constant, BinaryOp, Call, Return, UICall,
    StateInit, StateGet, StateSet,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop,
    IRClass, IRField, IRMethod, ClassInit, AttributeGet, AttributeSet, MethodCall,
    Jump, Branch
)

# Custom type for state to help emitter
STATE_TYPE = Type("laith.State")

class IRBuilder:
    def __init__(self, global_scope: Scope):
        self.global_scope = global_scope
        self.module = IRModule()
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBlock] = None
        self.value_counter = 0
        self.scope_values: List[Dict[str, IRValue]] = [{}]
        self.state_vars: List[set] = [set()]

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
        if is_state: self.state_vars[-1].add(value.id)

    def _is_state(self, val: IRValue) -> bool:
        if val.type == STATE_TYPE: return True
        for s in reversed(self.state_vars):
            if val.id in s: return True
        return False

    def _get_value(self, name: str) -> Optional[IRValue]:
        for scope in reversed(self.scope_values):
            if name in scope: return scope[name]
        return None

    def build(self, tree: ast.AST):
        global_init = IRFunction(name="global_init", return_type=VOID_TYPE, args=[])
        self.module.functions.append(global_init)
        self.current_function = global_init
        self.current_block = IRBlock(label="init")
        global_init.blocks.append(self.current_block)
        for stmt in tree.body: self.visit(stmt)
        self.current_function = None
        self.current_block = None
        return self.module

    def visit(self, node: ast.AST) -> Optional[IRValue]:
        method = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST):
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

    def _add_inst(self, inst: IRInstruction, node: Optional[ast.AST] = None):
        if node:
            inst.source_line = getattr(node, 'lineno', None)
            inst.source_col = getattr(node, 'col_offset', None)
        self.current_block.add_instruction(inst)

    def visit_Import(self, node: ast.Import): pass
    def visit_ImportFrom(self, node: ast.ImportFrom): pass

    def visit_JoinedStr(self, node: ast.JoinedStr) -> IRValue:
        if not node.values: return self.visit_expr(ast.Constant(value=""))
        res = self.visit_expr(node.values[0])
        for part in node.values[1:]:
            part_val = self.visit_expr(part)
            new_res = IRValue(id=self._next_id(), type=STR_TYPE)
            self._add_inst(BinaryOp(result=new_res, op="add", left=res, right=part_val), node)
            res = new_res
        return res

    def visit_FormattedValue(self, node: ast.FormattedValue) -> IRValue: return self.visit_expr(node.value)

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_f, prev_b = self.current_function, self.current_block
        symbol = self.global_scope.lookup(node.name)
        ir_class = IRClass(name=node.name, decorators=symbol.metadata.get("decorators", []) if symbol else [])
        self.module.classes.append(ir_class)
        class_scope = next((s for s in self.global_scope.children if s.name == node.name), self.global_scope)
        self._push_scope()
        if symbol:
            for f_name, f_type in symbol.metadata.get("fields", {}).items():
                ir_class.fields.append(IRField(name=f_name, type=f_type))
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ir_class.methods.append(self._build_method(item, class_scope, node.name))
        self._pop_scope()
        self.current_function, self.current_block = prev_f, prev_b

    def _build_method(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], class_scope: Scope, class_name: str) -> IRMethod:
        symbol = class_scope.lookup(node.name)
        method_scope = next((s for s in class_scope.children if s.name == node.name), class_scope)
        args = []
        self._push_scope()
        for arg in node.args.args:
            arg_symbol = method_scope.lookup(arg.arg)
            arg_val = IRValue(id=arg.arg, type=arg_symbol.type if arg_symbol else ANY_TYPE)
            args.append(arg_val); self._set_value(arg.arg, arg_val)
        method = IRMethod(name=node.name, return_type=symbol.type if symbol else VOID_TYPE, args=args,
                          is_async=isinstance(node, ast.AsyncFunctionDef), decorators=symbol.metadata.get("decorators", []) if symbol else [],
                          is_constructor=(node.name == "__init__"))
        entry = IRBlock(label="entry"); method.blocks.append(entry)
        pf, pb = self.current_function, self.current_block
        self.current_function, self.current_block = method, entry
        for stmt in node.body: self.visit(stmt)
        self.current_function, self.current_block = pf, pb
        self._pop_scope()
        return method

    def visit_FunctionDef(self, node: ast.FunctionDef): return self._visit_func(node, is_async=False)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef): return self._visit_func(node, is_async=True)

    def _visit_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        pf, pb = self.current_function, self.current_block
        symbol = self.global_scope.lookup(node.name)
        func_scope = next((s for s in self.global_scope.children if s.name == node.name), self.global_scope)
        args = []
        self._push_scope()
        for arg in node.args.args:
            asym = func_scope.lookup(arg.arg)
            aval = IRValue(id=arg.arg, type=asym.type if asym else ANY_TYPE)
            args.append(aval); self._set_value(arg.arg, aval)
        func = IRFunction(name=node.name, return_type=symbol.type if symbol else VOID_TYPE, args=args, is_async=is_async,
                          decorators=symbol.metadata.get("decorators", []) if symbol else [])
        self.module.functions.append(func); self.current_function = func
        entry = IRBlock(label="entry"); func.blocks.append(entry); self.current_block = entry
        for stmt in node.body: self.visit(stmt)
        self._pop_scope(); self.current_function, self.current_block = pf, pb

    def visit_Assign(self, node: ast.Assign):
        val = self.visit_expr(node.value)
        target = node.targets[0]
        if isinstance(target, ast.Name):
            is_state = self._is_state(val)
            self._set_value(target.id, val, is_state=is_state)
        elif isinstance(target, ast.Attribute):
            obj = self.visit_expr(target.value)
            self._add_inst(AttributeSet(obj=obj, attr_name=target.attr, value=val), node)

    def visit_Return(self, node: ast.Return):
        val = self.visit_expr(node.value) if node.value else None
        self._add_inst(Return(value=val), node)

    def visit_Try(self, node: ast.Try):
        # 1. Build body block
        body_block = IRBlock(label=f"try_body_{self._next_id()}")
        prev_block = self.current_block
        self.current_block = body_block
        for stmt in node.body: self.visit(stmt)
        
        # 2. Build handler block (Phase 12: assume one generic catch)
        handler_block = IRBlock(label=f"except_handler_{self._next_id()}")
        self.current_block = handler_block
        exc_name = None
        if node.handlers:
             handler = node.handlers[0]
             exc_name = handler.name
             if exc_name:
                  # Bind handler.name to a placeholder IRValue for the exception
                  self._set_value(exc_name, IRValue(id=exc_name, type=ANY_TYPE))
             for stmt in handler.body: self.visit(stmt)
        
        # 3. Add TryExcept instruction to parent block
        self.current_block = prev_block
        self._add_inst(TryExcept(body=body_block, handler=handler_block, exc_name=exc_name), node)

    def visit_Raise(self, node: ast.Raise):
        if node.exc:
            val = self.visit_expr(node.exc)
            self._add_inst(Raise(value=val), node)

    def visit_Expr(self, node: ast.Expr): self.visit_expr(node.value)

    def visit_Attribute(self, node: ast.Attribute) -> IRValue:
        obj = self.visit_expr(node.value)
        if self._is_state(obj) and node.attr == "value":
            res = IRValue(id=self._next_id(), type=ANY_TYPE)
            self._add_inst(StateGet(result=res, state_var=obj), node)
            return res
        res = IRValue(id=self._next_id(), type=ANY_TYPE)
        # If accessing a known state property of LabState
        if obj.type.name in ["LabState", "AppState"]: res.type = STATE_TYPE
        self._add_inst(AttributeGet(result=res, obj=obj, attr_name=node.attr), node)
        return res

    def visit_Constant(self, node: ast.Constant) -> IRValue:
        t = ANY_TYPE
        if isinstance(node.value, int): t = INT_TYPE
        elif isinstance(node.value, str): t = STR_TYPE
        elif isinstance(node.value, bool): t = BOOL_TYPE
        res = IRValue(id=self._next_id(), type=t)
        self._add_inst(Constant(result=res, value=node.value), node)
        return res

    def visit_Name(self, node: ast.Name) -> IRValue:
        val = self._get_value(node.id)
        if val is None:
            sym = self.global_scope.lookup(node.id)
            if sym and sym.kind == SymbolKind.CLASS: return IRValue(id=node.id, type=sym.type)
            raise Exception(f"Undefined {node.id}")
        return val

    def visit_BinOp(self, node: ast.BinOp) -> IRValue:
        l, r = self.visit_expr(node.left), self.visit_expr(node.right)
        op = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div"}[type(node.op)]
        res = IRValue(id=self._next_id(), type=l.type)
        self._add_inst(BinaryOp(result=res, op=op, left=l, right=r), node)
        return res

    def visit_Call(self, node: ast.Call) -> IRValue:
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "state":
                v = self.visit_expr(node.args[0])
                res = IRValue(id=self._next_id(), type=STATE_TYPE)
                self._add_inst(StateInit(result=res, initial_value=v), node)
                return res
            sym = self.global_scope.lookup(name)
            if sym and sym.kind == SymbolKind.CLASS and sym.type.name != "Channel":
                args = [self.visit_expr(a) for a in node.args]
                res = IRValue(id=self._next_id(), type=sym.type)
                self._add_inst(ClassInit(result=res, class_name=name, args=args), node)
                return res
            ui = {"Column", "Row", "Box", "Text", "Button"}
            if name in ui:
                kids = []; imms = []
                for a in node.args:
                    if isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id in ui: kids.append(a)
                    else: imms.append(a)
                kws = {}
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Lambda):
                        self._push_scope()
                        for la in kw.value.args.args: self._set_value(la.arg, IRValue(id=la.arg, type=ANY_TYPE))
                        pb = self.current_block
                        lb = IRBlock(label=f"{name}_{kw.arg}"); self.current_block = lb
                        self.visit_expr(kw.value.body); self.current_block = pb
                        self._pop_scope(); kws[kw.arg] = lb
                    else: kws[kw.arg] = self.visit_expr(kw.value)
                args = [self.visit_expr(a) for a in imms]; body = None
                if kids:
                    pb = self.current_block
                    body = IRBlock(label=f"{name}_body"); self.current_block = body
                    for k in kids: self.visit_expr(k)
                    self.current_block = pb
                self._add_inst(UICall(func_name=name, args=args, body=body, keywords=kws), node)
                return IRValue(id="void", type=VOID_TYPE)
            args = [self.visit_expr(a) for a in node.args]
            res = IRValue(id=self._next_id(), type=ANY_TYPE)
            self._add_inst(Call(result=res, func_name=name, args=args), node)
            return res
        if isinstance(node.func, ast.Attribute):
            obj = self.visit_expr(node.func.value)
            if self._is_state(obj) and node.func.attr == "set":
                v = self.visit_expr(node.args[0])
                self._add_inst(StateSet(state_var=obj, new_value=v), node)
                return IRValue(id="void", type=VOID_TYPE)
            args = [self.visit_expr(a) for a in node.args]
            res = IRValue(id=self._next_id(), type=ANY_TYPE)
            self._add_inst(MethodCall(result=res, obj=obj, method_name=node.func.attr, args=args), node)
            return res
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")

    def visit_expr(self, node: ast.AST) -> IRValue:
        res = self.visit(node)
        if res is None: raise Exception(f"No IRValue for {node}")
        return res
