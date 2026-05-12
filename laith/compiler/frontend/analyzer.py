import ast
import os
from typing import Optional, List, Union, Dict, Any, Set
from laith.compiler.frontend.symbols import (
    Scope, Symbol, SymbolKind, Type, 
    INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE
)
from laith.compiler.frontend.bridge import BridgeManager

class SemanticAnalyzer(ast.NodeVisitor):
    def __init__(self, sdk_path: Optional[str] = None):
        self.global_scope = Scope(name="global", kind="module")
        self.current_scope = self.global_scope
        self.current_class: Optional[Symbol] = None
        self.required_permissions: Set[str] = set()
        
        self._sdk_path = sdk_path
        self._bridge: Optional[BridgeManager] = None

        self._register_builtins()

    @property
    def bridge(self) -> Optional[BridgeManager]:
        if self._bridge is not None:
            return self._bridge
        sdk = self._sdk_path or os.environ.get("ANDROID_HOME")
        if sdk:
            self._bridge = BridgeManager(sdk)
        return self._bridge

    def _register_builtins(self):
        self.global_scope.define(Symbol("int", SymbolKind.CLASS, type=INT_TYPE))
        self.global_scope.define(Symbol("str", SymbolKind.CLASS, type=STR_TYPE))
        self.global_scope.define(Symbol("bool", SymbolKind.CLASS, type=BOOL_TYPE))
        self.global_scope.define(Symbol("print", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Column", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Row", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Text", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Button", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("TextField", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Checkbox", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Switch", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Slider", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Scaffold", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("TopAppBar", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("BottomAppBar", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("NavigationBar", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("NavigationBarItem", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("FloatingActionButton", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Spacer", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Icon", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Image", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Dialog", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("AlertDialog", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Snackbar", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("ModalBottomSheet", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("state", SymbolKind.FUNCTION, type=ANY_TYPE))
        self.global_scope.define(Symbol("periodic_task", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("native", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("context", SymbolKind.VARIABLE, type=Type("android.content.Context")))
        self.global_scope.define(Symbol("vibrate", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("has_permission", SymbolKind.FUNCTION, type=BOOL_TYPE))
        self.global_scope.define(Symbol("get_location", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("request_location_permission", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Navigator", SymbolKind.CLASS, type=Type("laith.Navigator")))
        self.global_scope.define(Symbol("route", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("on_mount", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("on_dispose", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("effect", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Preferences", SymbolKind.CLASS, type=Type("laith.Preferences")))
        self.global_scope.define(Symbol("FileStorage", SymbolKind.CLASS, type=Type("laith.FileStorage")))
        self.global_scope.define(Symbol("on_resume", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("on_pause", SymbolKind.FUNCTION, type=VOID_TYPE))
        self.global_scope.define(Symbol("Theme", SymbolKind.FUNCTION, type=VOID_TYPE))

    def analyze(self, tree: ast.AST):
        self.visit(tree)
        # Store inferred permissions in global scope metadata for CLI to pick up
        self.global_scope.metadata["required_permissions"] = list(self.required_permissions)
        return self.global_scope

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == "vibrate":
                self.required_permissions.add("android.permission.VIBRATE")
            elif node.func.id in ["get_location", "request_location_permission"]:
                self.required_permissions.add("android.permission.ACCESS_FINE_LOCATION")
                self.required_permissions.add("android.permission.ACCESS_COARSE_LOCATION")
        self.visit(node.func)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        parent_scope = self.current_scope
        self.current_scope = parent_scope.create_child(name=node.name, kind="class")
        fields = {}; methods = {}
        cls_symbol = Symbol(name=node.name, kind=SymbolKind.CLASS, type=Type(node.name),
                            metadata={"fields": fields, "methods": methods, "decorators": self._parse_decorators(node.decorator_list)})
        self.current_class = cls_symbol
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(item)
                methods[item.name] = {"is_async": isinstance(item, ast.AsyncFunctionDef), "is_constructor": item.name == "__init__"}
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name): fields[item.target.id] = self._resolve_type(item.annotation)
        self.current_class = None
        self.current_scope = parent_scope
        self.current_scope.define(cls_symbol)

    def visit_FunctionDef(self, node: ast.FunctionDef): self._visit_func(node, is_async=False)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef): self._visit_func(node, is_async=True)

    def _visit_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        is_method = self.current_scope.kind == "class"
        return_type = self._resolve_type(node.returns) if node.returns else VOID_TYPE
        decorators = self._parse_decorators(node.decorator_list)
        func_symbol = Symbol(name=node.name, kind=SymbolKind.FUNCTION, type=return_type, is_async=is_async,
                            metadata={"decorators": decorators, "is_method": is_method})
        self.current_scope.define(func_symbol)
        parent_scope = self.current_scope
        self.current_scope = parent_scope.create_child(name=node.name)
        for i, arg in enumerate(node.args.args):
            arg_type = ANY_TYPE
            if i == 0 and is_method: arg_type = Type(parent_scope.name)
            elif arg.annotation: arg_type = self._resolve_type(arg.annotation)
            self.current_scope.define(Symbol(name=arg.arg, kind=SymbolKind.PARAMETER, type=arg_type))
        for stmt in node.body: self.visit(stmt)
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

    def visit_Attribute(self, node: ast.Attribute):
        self.visit(node.value)
        if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
             fields = self.current_class.metadata.get("fields", {})
             if node.attr not in fields: fields[node.attr] = ANY_TYPE
        return ANY_TYPE

    def visit_Name(self, node: ast.Name):
        symbol = self.current_scope.lookup(node.id)
        if not symbol and self.bridge:
            fqn = self.bridge.find_class_by_short_name(node.id)
            if fqn:
                metadata = self.bridge.lookup_class(fqn)
                if metadata:
                    symbol = Symbol(name=node.id, kind=SymbolKind.CLASS, type=Type(fqn), metadata=metadata)
                    self.global_scope.define(symbol)
        return symbol

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets: self.visit(target)
        self.visit(node.value)
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name): return
        target = node.targets[0]
        if not self.current_scope.lookup(target.id):
            self.current_scope.define(Symbol(name=target.id, kind=SymbolKind.VARIABLE, type=ANY_TYPE))

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.visit(node.target)
        if node.value: self.visit(node.value)
        if isinstance(node.target, ast.Name):
            self.current_scope.define(Symbol(name=node.target.id, kind=SymbolKind.VARIABLE, type=self._resolve_type(node.annotation)))

    def visit_Try(self, node: ast.Try):
        # Visit body
        for stmt in node.body: self.visit(stmt)
        # Visit handlers
        for handler in node.handlers:
            if handler.name:
                 # Define the exception variable in the current scope
                 self.current_scope.define(Symbol(name=handler.name, kind=SymbolKind.VARIABLE, type=ANY_TYPE))
            for stmt in handler.body: self.visit(stmt)
        # We don't support 'else' or 'finally' yet in Phase 12

    def visit_Raise(self, node: ast.Raise):
        if node.exc: self.visit(node.exc)

    def _resolve_type(self, node: Optional[ast.AST]) -> Type:
        if isinstance(node, ast.Name):
            mapping = {"int": INT_TYPE, "str": STR_TYPE, "bool": BOOL_TYPE, "None": VOID_TYPE}
            if node.id in mapping: return mapping[node.id]
        return ANY_TYPE

class Parser:
    @staticmethod
    def parse(source: str) -> ast.AST: return ast.parse(source)
