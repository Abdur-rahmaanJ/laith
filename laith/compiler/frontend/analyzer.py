import ast
from typing import Optional, List, Union
from laith.compiler.frontend.symbols import (
    Scope, Symbol, SymbolKind, Type, 
    INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE
)

class SemanticError(Exception):
    def __init__(self, message: str, node: ast.AST):
        super().__init__(f"{message} (line {node.lineno}, col {node.col_offset})")
        self.node = node

class SemanticAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        
        # Register built-ins
        self._register_builtins()

    def _register_builtins(self):
        self.global_scope.define(Symbol("int", SymbolKind.CLASS, type=INT_TYPE))
        self.global_scope.define(Symbol("str", SymbolKind.CLASS, type=STR_TYPE))
        self.global_scope.define(Symbol("bool", SymbolKind.CLASS, type=BOOL_TYPE))
        self.global_scope.define(Symbol("print", SymbolKind.FUNCTION, type=VOID_TYPE))
        
        # UI components
        self.global_scope.define(Symbol("Column", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Row", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Text", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Button", SymbolKind.FUNCTION, type=VOID_TYPE))
        
        # State management
        self.global_scope.define(Symbol("state", SymbolKind.FUNCTION, type=ANY_TYPE))
        
        # Background tasks
        self.global_scope.define(Symbol("periodic_task", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("foreground_service", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("start_service", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("stop_service", SymbolKind.FUNCTION, type=VOID_TYPE))
        
        # IPC & Channels
        self.global_scope.define(Symbol("Channel", SymbolKind.CLASS, type=ANY_TYPE))
        
        # Native compilation
        self.global_scope.define(Symbol("native", SymbolKind.FUNCTION, type=VOID_TYPE))

    def analyze(self, tree: ast.AST):
        self.visit(tree)
        return self.global_scope

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self._visit_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self._visit_func(node, is_async=True)

    def _visit_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        # Determine return type
        return_type = self._resolve_type(node.returns) if node.returns else VOID_TYPE
        
        # Process decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                name = dec.func.id
                args = {k.arg: ast.literal_eval(k.value) for k in dec.keywords if k.arg}
                decorators.append({"name": name, "args": args})
            elif isinstance(dec, ast.Name):
                decorators.append({"name": dec.id, "args": {}})

        func_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.FUNCTION,
            type=return_type,
            is_async=is_async,
            metadata={"decorators": decorators}
        )
        self.current_scope.define(func_symbol)
        
        # Enter function scope
        parent_scope = self.current_scope
        self.current_scope = parent_scope.create_child(name=node.name)
        
        # Process arguments
        for arg in node.args.args:
            arg_type = self._resolve_type(arg.annotation) if arg.annotation else ANY_TYPE
            arg_symbol = Symbol(name=arg.arg, kind=SymbolKind.PARAMETER, type=arg_type)
            self.current_scope.define(arg_symbol)
            
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_scope = parent_scope

    def visit_Assign(self, node: ast.Assign):
        # For MVP, we only support simple assignments to names
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            # We can expand this later
            return

        target = node.targets[0]
        name = target.id
        
        # In a real compiler, we'd do type inference here
        # For now, if it's a new variable, we define it as ANY if not previously known
        symbol = self.current_scope.lookup(name)
        if not symbol:
            symbol = Symbol(name=name, kind=SymbolKind.VARIABLE, type=ANY_TYPE)
            self.current_scope.define(symbol)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if not isinstance(node.target, ast.Name):
            return
            
        name = node.target.id
        var_type = self._resolve_type(node.annotation)
        
        symbol = Symbol(name=name, kind=SymbolKind.VARIABLE, type=var_type)
        self.current_scope.define(symbol)

    def _resolve_type(self, node: Optional[ast.AST]) -> Type:
        if isinstance(node, ast.Name):
            if node.id == "int": return INT_TYPE
            if node.id == "str": return STR_TYPE
            if node.id == "bool": return BOOL_TYPE
            if node.id == "None": return VOID_TYPE
        
        # Fallback for now
        return ANY_TYPE

class Parser:
    @staticmethod
    def parse(source: str) -> ast.AST:
        return ast.parse(source)
