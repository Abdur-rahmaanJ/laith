import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.errors import CompileError


class TestDoctor:
    def test_basic_analysis(self):
        code = """
def main_ui():
    Text("Hello")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        assert global_scope.lookup("Text") is not None
        assert global_scope.lookup("main_ui") is not None

    def test_undefined_identifier_reports(self):
        code = """
def main_ui():
    x = undefined_var
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        builder = IRBuilder(global_scope)
        with pytest.raises(CompileError):
            builder.build(tree)

    def test_undefined_name_in_expression(self):
        code = """
def main_ui():
    x = 10 + y
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)

        builder = IRBuilder(global_scope)
        with pytest.raises(CompileError):
            builder.build(tree)
