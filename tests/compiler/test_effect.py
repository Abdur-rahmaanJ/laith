import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_effect_basic():
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

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "effectKey" in kotlin_code or "_effectKey" in kotlin_code


def test_effect_called():
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

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code


def test_effect_with_button():
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

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "Button" in kotlin_code
    assert "Column" in kotlin_code
