import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_theme_basic():
    code = """
def main_ui():
    Theme(
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

    assert "MaterialTheme" in kotlin_code
    assert "Column" in kotlin_code


def test_theme_with_colors():
    code = """
def main_ui():
    Theme(
        primary="#FF6200EE",
        body=Text("Styled")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "MaterialTheme" in kotlin_code
    assert "lightColorScheme" in kotlin_code
    assert "darkColorScheme" in kotlin_code


def test_theme_dynamic_colors():
    code = """
def main_ui():
    Theme(
        use_dynamic_colors=True,
        body=Text("Dynamic")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "dynamicDarkColorScheme" in kotlin_code
    assert "dynamicLightColorScheme" in kotlin_code


def test_theme_dark_light():
    code = """
def main_ui():
    Theme(
        primary="#FF6200EE",
        dark_primary="#FFBB86FC",
        body=Text("Styled")
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "isSystemInDarkTheme" in kotlin_code
    assert "FFBB86FC" in kotlin_code or "FF6200EE" in kotlin_code


def test_theme_is_composable():
    code = """
def main_ui():
    Theme(
        body=Button("Themed Button", on_click=lambda: print("click"))
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "MaterialTheme" in kotlin_code
    assert "Button" in kotlin_code
