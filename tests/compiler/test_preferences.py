import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_preferences_create():
    code = """
def main_ui():
    prefs = Preferences("my_app")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "getSharedPreferences" in kotlin_code


def test_preferences_get():
    code = """
def main_ui():
    prefs = Preferences("app")
    val = prefs.get("key", "default")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "getSharedPreferences" in kotlin_code
    assert "getString" in kotlin_code


def test_preferences_set():
    code = """
def main_ui():
    prefs = Preferences("app")
    prefs.set("key", "value")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "edit" in kotlin_code
    assert "putString" in kotlin_code


def test_preferences_remove():
    code = """
def main_ui():
    prefs = Preferences("app")
    prefs.remove("key")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "remove" in kotlin_code


def test_preferences_contains():
    code = """
def main_ui():
    prefs = Preferences("app")
    has = prefs.contains("key")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "contains" in kotlin_code
