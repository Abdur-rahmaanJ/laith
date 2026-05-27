import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestNavigator:
    def test_navigator_push(self, fresh_emitter):
        code = """
def home():
    Navigator.push(settings, title="Hello")

def settings():
    pass
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "navigatorPush" in kotlin

    def test_navigator_pop(self, fresh_emitter):
        code = """
def main_ui():
    Navigator.pop()
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "navigatorPop" in kotlin

    def test_navigator_push_with_kwargs(self, fresh_emitter):
        code = """
def home():
    Navigator.push(settings, title="World", id=42)

def settings():
    pass
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "navigatorPush" in kotlin
