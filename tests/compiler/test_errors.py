import pytest
from laith.compiler.errors import (
    CompileError, SourceLocation, UndefinedSymbolError,
    TypeError, UnsupportedFeatureError,
)
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.errors import CompileError as CompileErrorClass

def test_compile_error_creation():
    loc = SourceLocation(line=5, col=10)
    err = CompileError("Something went wrong", location=loc, hint="Try fixing X")
    assert err.message == "Something went wrong"
    assert err.location.line == 5
    assert err.hint == "Try fixing X"

def test_compile_error_with_source_context():
    source = "x = 1 + 2\nprint(x)\nz = y + 1"
    loc = SourceLocation(line=3, col=4, source=source)
    formatted = loc.format(context_lines=1)
    assert "3" in formatted
    assert "z = y + 1" in formatted
    assert "^" in formatted

def test_undefined_symbol_error():
    loc = SourceLocation(line=3, col=4)
    err = UndefinedSymbolError("my_var", location=loc)
    assert "my_var" in err.message
    assert err.hint is not None
    assert "define" in err.hint

def test_type_error():
    loc = SourceLocation(line=2, col=8)
    err = TypeError("Type mismatch", expected="int", got="str", location=loc)
    assert "Type mismatch" in err.message
    assert "int" in err.hint
    assert "str" in err.hint

def test_unsupported_feature_error():
    loc = SourceLocation(line=1, col=0)
    err = UnsupportedFeatureError("async comprehensions", location=loc)
    assert "async comprehensions" in err.message

def test_analyzer_undefined_symbol():
    code = """
def foo():
    x = unknown_var + 1
    return x
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    with pytest.raises(CompileErrorClass) as excinfo:
        builder.build(tree)
    assert "unknown_var" in str(excinfo.value)

def test_ir_builder_undefined_symbol():
    code = """
def foo():
    x = 10
    return x + y
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    with pytest.raises(CompileErrorClass) as excinfo:
        builder.build(tree)
    assert "y" in str(excinfo.value)

def test_source_location_format():
    source = "line1\nline2\nline3\nline4\nline5"
    loc = SourceLocation(line=3, col=2, source=source)
    formatted = loc.format(context_lines=1)
    assert "line2" in formatted
    assert "line3" in formatted
    assert "line4" in formatted
    assert "^" in formatted

def test_error_no_location():
    err = CompileError("Simple error")
    assert str(err) == "[bold red]Error:[/bold red] Simple error"

def test_error_with_all_fields():
    loc = SourceLocation(line=1, col=0, source="bad code")
    err = CompileError("Bad code", location=loc, hint="Write good code instead")
    assert "Bad code" in str(err)
    assert "good code" in str(err)
    assert "bad code" in str(err)
