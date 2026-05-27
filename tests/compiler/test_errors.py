import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.errors import CompileError, UndefinedSymbolError


class TestCompileError:
    def test_error_creation(self):
        from laith.compiler.errors import SourceLocation
        loc = SourceLocation(line=5, col=10)
        err = CompileError("Something went wrong", location=loc, hint="Try fixing X")
        assert err.message == "Something went wrong"
        assert err.location.line == 5
        assert err.hint == "Try fixing X"

    def test_error_with_source_context(self):
        from laith.compiler.errors import SourceLocation
        source = "x = 1 + 2\nprint(x)\nz = y + 1"
        loc = SourceLocation(line=3, col=4, source=source)
        formatted = loc.format(context_lines=1)
        assert "z = y + 1" in formatted

    def test_undefined_symbol_error(self):
        from laith.compiler.errors import SourceLocation
        err = UndefinedSymbolError("my_var")
        assert "my_var" in err.message

    def test_error_no_location(self):
        err = CompileError("Simple error")
        assert "Simple error" in str(err)


class TestIRBuilderErrors:
    def test_undefined_symbol_in_ir(self):
        code = """
def foo():
    x = unknown_var + 1
    return x
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)

        with pytest.raises(CompileError) as excinfo:
            builder.build(tree)
        assert "unknown_var" in str(excinfo.value)

    def test_undefined_variable_in_expression(self):
        code = """
def foo():
    x = 10
    return x + y
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)

        with pytest.raises(CompileError) as excinfo:
            builder.build(tree)
        assert "y" in str(excinfo.value)


class TestSourceLocation:
    def test_format_with_context(self):
        from laith.compiler.errors import SourceLocation
        source = "line1\nline2\nline3\nline4\nline5"
        loc = SourceLocation(line=3, col=2, source=source)
        formatted = loc.format(context_lines=1)
        assert "line2" in formatted
        assert "line4" in formatted
