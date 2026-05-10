import pytest
import ast
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.frontend.symbols import SymbolKind, INT_TYPE, STR_TYPE

def test_basic_symbol_resolution():
    code = """
def hello(name: str) -> int:
    x: int = 10
    print(name)
    return x
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    
    # Check function symbol
    hello_sym = global_scope.lookup("hello")
    assert hello_sym is not None
    assert hello_sym.kind == SymbolKind.FUNCTION
    assert hello_sym.type == INT_TYPE
    
    # Check scope hierarchy
    assert len(global_scope.children) == 1
    func_scope = global_scope.children[0]
    assert func_scope.name == "hello"
    
    # Check parameter
    name_sym = func_scope.lookup("name")
    assert name_sym is not None
    assert name_sym.kind == SymbolKind.PARAMETER
    assert name_sym.type == STR_TYPE
    
    # Check local variable
    x_sym = func_scope.lookup("x")
    assert x_sym is not None
    assert x_sym.kind == SymbolKind.VARIABLE
    assert x_sym.type == INT_TYPE

def test_async_function():
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
