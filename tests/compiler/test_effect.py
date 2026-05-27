import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestEffect:
    def test_basic_effect(self, fresh_emitter):
        code = """
def main_ui():
    count = state(0)
    effect(count, lambda old, new: print(new))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        non_import_lines = [l for l in kotlin.split("\n") if not l.startswith("import ")]
        assert any("LaunchedEffect" in l for l in non_import_lines)

    def test_effect_called(self, fresh_emitter):
        code = """
def main_ui():
    count = state(0)
    effect(count, lambda old, new: print(old + new))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "LaunchedEffect" in kotlin

    def test_effect_with_button(self, fresh_emitter):
        code = """
def main_ui():
    text = state("")
    effect(text, lambda old, new: print(new))
    Column(
        Button("Click")
    )
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "LaunchedEffect" in kotlin
        assert "Button" in kotlin
        assert "Column" in kotlin
