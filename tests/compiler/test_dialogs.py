import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_dialog():
    code = """
def main_ui():
    Dialog(
        Text("Hello"),
        on_dismiss=lambda: print("dismissed"),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Dialog" in kotlin_code
    assert "onDismissRequest" in kotlin_code


def test_alert_dialog():
    code = """
def main_ui():
    AlertDialog(
        title="Confirm",
        text="Are you sure?",
        on_confirm=lambda: print("confirmed"),
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


def test_snackbar():
    code = """
def main_ui():
    Snackbar("Hello")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Snackbar" in kotlin_code


def test_modal_bottom_sheet():
    code = """
def main_ui():
    ModalBottomSheet(
        Text("Content"),
        on_dismiss=lambda: print("dismissed"),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ModalBottomSheet" in kotlin_code


def test_dialog_in_scaffold():
    code = """
def main_ui():
    show = state(False)
    Scaffold(
        body=Button("Open", on_click=lambda: show.set(True)),
    )
    if show:
        Dialog(on_dismiss=lambda: print("dismissed"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Dialog" in kotlin_code
    assert "Scaffold" in kotlin_code
