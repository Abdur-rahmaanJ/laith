import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_scaffold_basic():
    code = """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        body=Column(
            Text("Hello")
        )
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Scaffold" in kotlin_code
    assert "topBar" in kotlin_code or "top_bar" in kotlin_code


def test_scaffold_with_bottom_bar():
    code = """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        bottom_bar=BottomAppBar(),
        body=Text("Content")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Scaffold" in kotlin_code


def test_scaffold_with_fab():
    code = """
def main_ui():
    Scaffold(
        fab=FloatingActionButton(),
        body=Text("Content")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Scaffold" in kotlin_code


def test_spacer():
    code = """
def main_ui():
    Column(
        Text("Top"),
        Spacer(),
        Text("Bottom"),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Spacer" in kotlin_code
    assert "Modifier.weight" in kotlin_code


def test_icon():
    code = """
def main_ui():
    Icon()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Icon" in kotlin_code
    assert "contentDescription" in kotlin_code


def test_navigation_bar():
    code = """
def main_ui():
    NavigationBar(
        NavigationBarItem()
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "NavigationBar" in kotlin_code


def test_top_app_bar():
    code = """
def main_ui():
    TopAppBar()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "TopAppBar" in kotlin_code or "TopAppBar" in kotlin_code
