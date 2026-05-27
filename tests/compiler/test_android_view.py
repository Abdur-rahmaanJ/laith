import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestAndroidView:
    def test_basic(self, fresh_emitter):
        code = """
def main_ui():
    AndroidView(factory=lambda: context)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "AndroidView" in kotlin

    def test_is_composable(self, fresh_emitter):
        code = """
def main_ui():
    AndroidView(factory=lambda: context)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "@Composable" in kotlin

    def test_with_context(self, fresh_emitter):
        code = """
def main_ui():
    ctx = context
    AndroidView(factory=lambda: ctx)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "AndroidView" in kotlin
