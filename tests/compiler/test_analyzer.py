import pytest
import ast
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.frontend.symbols import SymbolKind, INT_TYPE, STR_TYPE


class TestBasicSymbolResolution:
    def test_function_symbol(self):
        code = """
def hello(name: str) -> int:
    x: int = 10
    print(name)
    return x
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        hello_sym = global_scope.lookup("hello")
        assert hello_sym is not None
        assert hello_sym.kind == SymbolKind.FUNCTION
        assert hello_sym.type == INT_TYPE

        assert len(global_scope.children) >= 1
        func_scope = global_scope.children[0]
        assert func_scope.name == "hello"

        name_sym = func_scope.lookup("name")
        assert name_sym is not None
        assert name_sym.kind == SymbolKind.PARAMETER
        assert name_sym.type == STR_TYPE

        x_sym = func_scope.lookup("x")
        assert x_sym is not None
        assert x_sym.kind == SymbolKind.VARIABLE
        assert x_sym.type == INT_TYPE


class TestAsyncFunction:
    def test_async_function_detection(self):
        code = """
async def fetch_data() -> str:
    return "data"
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        fetch_sym = global_scope.lookup("fetch_data")
        assert fetch_sym is not None
        assert fetch_sym.is_async is True
        assert fetch_sym.type == STR_TYPE


class TestScopeNesting:
    def test_nested_scopes(self):
        code = """
def outer() -> int:
    x = 10
    def inner() -> int:
        return x
    return inner()
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        outer = global_scope.lookup("outer")
        assert outer is not None

    def test_builtin_symbols_available(self):
        analyzer = SemanticAnalyzer()
        builtins = ["int", "str", "bool", "print", "state", "Text", "Button"]
        for name in builtins:
            sym = analyzer.global_scope.lookup(name)
            assert sym is not None, f"Builtin {name} not found"

    def test_variable_defined_in_assign(self):
        code = """
def f():
    x = 42
    return x
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        func_scope = global_scope.children[0]
        x_sym = func_scope.lookup("x")
        assert x_sym is not None
        assert x_sym.kind == SymbolKind.VARIABLE


class TestClassAnalysis:
    def test_class_definition(self):
        code = """
class MyClass:
    def __init__(self):
        pass
    def method(self) -> int:
        return 42
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        cls = global_scope.lookup("MyClass")
        assert cls is not None
        assert cls.kind == SymbolKind.CLASS


class TestPermissionInference:
    def test_vibrate_permission(self):
        code = """
def f():
    vibrate(500)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        assert "android.permission.VIBRATE" in global_scope.metadata.get("required_permissions", [])

    def test_location_permission(self):
        code = """
def f():
    get_location(lambda lat, lon: print(lat))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        perms = global_scope.metadata.get("required_permissions", [])
        assert "android.permission.ACCESS_FINE_LOCATION" in perms


class TestDecoratorParsing:
    def test_simple_decorator(self):
        code = """
@route(path="/home")
def home():
    pass
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        home = global_scope.lookup("home")
        assert home is not None
        decs = home.metadata.get("decorators", [])
        assert len(decs) == 1
        assert decs[0]["name"] == "route"
