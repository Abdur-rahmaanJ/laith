import ast
import os
from typing import Optional, List, Union, Dict, Any
from laith.compiler.frontend.symbols import (
    Scope, Symbol, SymbolKind, Type, 
    INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE
)
from laith.compiler.frontend.bridge import BridgeManager

class SemanticError(Exception):
    def __init__(self, message: str, node: ast.AST):
        super().__init__(f"{message} (line {node.lineno}, col {node.col_offset})")
        self.node = node

class SemanticAnalyzer(ast.NodeVisitor):
    def __init__(self, sdk_path: Optional[str] = None):
        self.global_scope = Scope(name="global", kind="module")
        self.current_scope = self.global_scope
        
        # Initialize bridge if SDK path provided
        self.bridge = None
        if sdk_path:
             self.bridge = BridgeManager(sdk_path)
        elif os.environ.get("ANDROID_HOME"):
             self.bridge = BridgeManager(os.environ.get("ANDROID_HOME"))

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

    def visit_ClassDef(self, node: ast.ClassDef):
        # Create a new scope for the class
        parent_scope = self.current_scope
        self.current_scope = parent_scope.create_child(name=node.name, kind="class")
        
        # Register fields and methods in metadata
        fields = {}
        methods = {}
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Methods
                is_constructor = item.name == "__init__"
                # Visit the method to analyze its body
                self.visit(item)
                # Store method info
                methods[item.name] = {
                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                    "is_constructor": is_constructor
                }
            elif isinstance(item, ast.AnnAssign):
                # Class fields (if any)
                if isinstance(item.target, ast.Name):
                    fields[item.target.id] = self._resolve_type(item.annotation)
        
        self.current_scope = parent_scope
        
        # Define the class in the parent scope
        cls_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.CLASS,
            type=Type(node.name),
            metadata={
                "fields": fields,
                "methods": methods,
                "decorators": self._parse_decorators(node.decorator_list)
            }
        )
        self.current_scope.define(cls_symbol)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self._visit_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self._visit_func(node, is_async=True)

    def _visit_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        is_method = self.current_scope.kind == "class"
        
        # Determine return type
        return_type = self._resolve_type(node.returns) if node.returns else VOID_TYPE
        
        # Process decorators
        decorators = self._parse_decorators(node.decorator_list)

        func_symbol = Symbol(
            name=node.name,
            kind=SymbolKind.FUNCTION,
            type=return_type,
            is_async=is_async,
            metadata={
                "decorators": decorators,
                "is_method": is_method
            }
        )
        self.current_scope.define(func_symbol)
        
        # Enter function scope
        parent_scope = self.current_scope
        self.current_scope = parent_scope.create_child(name=node.name)
        
        # Process arguments
        for i, arg in enumerate(node.args.args):
            # If it's the first arg of a method, it's 'self'
            arg_type = ANY_TYPE
            if i == 0 and is_method:
                arg_type = Type(parent_scope.name) # Self type is the class name
            elif arg.annotation:
                arg_type = self._resolve_type(arg.annotation)
            
            arg_symbol = Symbol(name=arg.arg, kind=SymbolKind.PARAMETER, type=arg_type)
            self.current_scope.define(arg_symbol)
            
        # Visit body
        for stmt in node.body:
            self.visit(stmt)
            
        self.current_scope = parent_scope

    def _parse_decorators(self, decorator_list: List[ast.AST]) -> List[Dict[str, Any]]:
        decorators = []
        for dec in decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                name = dec.func.id
                args = {k.arg: ast.literal_eval(k.value) for k in dec.keywords if k.arg}
                decorators.append({"name": name, "args": args})
            elif isinstance(dec, ast.Name):
                decorators.append({"name": dec.id, "args": {}})
        return decorators

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            symbol = self.current_scope.lookup(name)
            if not symbol and self.bridge:
                # Try to resolve via Android SDK
                fqn = self.bridge.find_class_by_short_name(name)
                if fqn:
                    metadata = self.bridge.lookup_class(fqn)
                    if metadata:
                        # Define class symbol dynamically
                        symbol = Symbol(
                            name=name,
                            kind=SymbolKind.CLASS,
                            type=Type(fqn),
                            metadata=metadata
                        )
                        self.global_scope.define(symbol)

        # Generic visit to children (arguments)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # We need to know the type of the base to resolve the attribute
        # For MVP, assume it's an instance attribute
        return ANY_TYPE

    def visit_Assign(self, node: ast.Assign):
        # Visit value to resolve symbols
        self.visit(node.value)

        # For MVP, we only support simple assignments to names
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return

        target = node.targets[0]
        name = target.id
        
        symbol = self.current_scope.lookup(name)
        if not symbol:
            symbol = Symbol(name=name, kind=SymbolKind.VARIABLE, type=ANY_TYPE)
            self.current_scope.define(symbol)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value:
             self.visit(node.value)

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
