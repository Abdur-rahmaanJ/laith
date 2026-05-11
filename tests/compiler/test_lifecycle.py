import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_on_mount():
    code = """
def main_ui():
    on_mount(lambda: print("mounted"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "print" in kotlin_code


def test_on_dispose():
    code = """
def main_ui():
    on_dispose(lambda: print("cleaned"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "DisposableEffect" in kotlin_code
    assert "onDispose" in kotlin_code
    assert "print" in kotlin_code


def test_on_mount_multiple_statements():
    code = """
def main_ui():
    on_mount(lambda: print("start"))
    Button("Click")
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


def test_on_mount_in_composable():
    code = """
def main_ui():
    on_mount(lambda: print("mounted"))
    Column(
        Text("Hello")
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
    assert "Column" in kotlin_code
    assert "Text" in kotlin_code
