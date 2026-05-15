import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_android_view_basic():
    code = """
def main_ui():
    AndroidView(lambda ctx: print(ctx))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "AndroidView" in kotlin_code
    assert "factory" in kotlin_code


def test_android_view_is_composable():
    code = """
def main_ui():
    AndroidView(lambda ctx: print(ctx))
    Text("Below")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "AndroidView" in kotlin_code
    assert "@Composable" in kotlin_code


def test_android_view_with_context():
    code = """
def main_ui():
    AndroidView(lambda ctx: Button("Native", on_click=lambda: print("click")))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "AndroidView" in kotlin_code
