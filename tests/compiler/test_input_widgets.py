import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_textfield_emission():
    code = """
def main_ui():
    text = state("")
    TextField(value=text, on_value_change=text.set)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "OutlinedTextField" in kotlin_code
    assert "onValueChange" in kotlin_code


def test_checkbox_emission():
    code = """
def main_ui():
    checked = state(False)
    Checkbox(checked=checked, on_checked_change=checked.set)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Checkbox" in kotlin_code
    assert "onCheckedChange" in kotlin_code


def test_switch_emission():
    code = """
def main_ui():
    enabled = state(False)
    Switch(checked=enabled, on_checked_change=enabled.set)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Switch" in kotlin_code
    assert "onCheckedChange" in kotlin_code


def test_slider_emission():
    code = """
def main_ui():
    volume = state(0.5)
    Slider(value=volume, on_value_change=volume.set)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Slider" in kotlin_code
    assert "onValueChange" in kotlin_code


def test_all_widgets_in_ui_set():
    code = """
def main_ui():
    text = state("")
    checked = state(False)
    volume = state(0.5)
    Column(
        TextField(value=text, on_value_change=text.set),
        Checkbox(checked=checked, on_checked_change=checked.set),
        Switch(checked=checked, on_checked_change=checked.set),
        Slider(value=volume, on_value_change=volume.set),
    )
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "OutlinedTextField" in kotlin_code
    assert "Checkbox" in kotlin_code
    assert "Switch" in kotlin_code
    assert "Slider" in kotlin_code
    assert "Column" in kotlin_code


def test_textfield_label():
    code = """
def main_ui():
    text = state("")
    TextField(value=text, on_value_change=text.set, label="Name")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "OutlinedTextField" in kotlin_code
    assert "label" in kotlin_code or "Name" in kotlin_code
