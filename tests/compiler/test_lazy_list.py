import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_lazy_column_basic():
    code = """
def main_ui():
    items = [1, 2, 3]
    LazyColumn(
        items=items,
        body=lambda item: Text(item)
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LazyColumn" in kotlin_code
    assert "items" in kotlin_code
    assert "Text(item.toString())" in kotlin_code or "Text(item)" in kotlin_code


def test_lazy_row_basic():
    code = """
def main_ui():
    items = [1, 2, 3]
    LazyRow(
        items=items,
        body=lambda item: Text(item)
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LazyRow" in kotlin_code
    assert "items" in kotlin_code
    assert "Text(item.toString())" in kotlin_code or "Text(item)" in kotlin_code


def test_lazy_column_empty():
    code = """
def main_ui():
    LazyColumn(
        items=[],
        body=lambda item: Text(item)
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LazyColumn" in kotlin_code


def test_lazy_row_is_composable():
    code = """
def main_ui():
    items = ["a", "b"]
    LazyRow(
        items=items,
        body=lambda item: Button(item, on_click=lambda: print("click"))
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LazyRow" in kotlin_code
    assert "Button" in kotlin_code
