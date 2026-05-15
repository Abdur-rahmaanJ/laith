import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_dialog_action():
    code = """
def main_ui():
    AlertDialog(
        title="Confirm",
        text="Delete?",
        on_confirm=lambda: print("deleted"),
        on_dismiss=lambda: print("cancelled"),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "AlertDialog" in kotlin_code
    assert "confirmButton" in kotlin_code


def test_multiple_effects():
    code = """
def main_ui():
    a = state(1)
    b = state(2)
    effect(a, lambda old, new: print(new))
    effect(b, lambda old, new: print(new))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert kotlin_code.count("LaunchedEffect") >= 2


def test_on_mount_twice():
    code = """
def main_ui():
    on_mount(lambda: print("first"))
    on_mount(lambda: print("second"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert kotlin_code.count("LaunchedEffect") >= 2


def test_preferences_exists_check():
    code = """
def main_ui():
    prefs = Preferences("test")
    if prefs.contains("key"):
        Text("found")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "contains" in kotlin_code


def test_file_storage_exists():
    code = """
def main_ui():
    if FileStorage.exists("config.json"):
        Text("config exists")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "exists" in kotlin_code


def test_theme_no_colors():
    code = """
def main_ui():
    Theme(
        body=Text("Plain"),
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
    assert "Text" in kotlin_code


def test_on_dispose_with_state():
    code = """
def main_ui():
    timer = state(None)
    on_mount(lambda: timer.set("started"))
    on_dispose(lambda: timer.set("stopped"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "LaunchedEffect" in kotlin_code
    assert "DisposableEffect" in kotlin_code
    assert "onDispose" in kotlin_code


def test_file_storage_delete():
    code = """
def main_ui():
    if FileStorage.exists("tmp.txt"):
        FileStorage.delete("tmp.txt")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "exists" in kotlin_code
    assert "delete" in kotlin_code
