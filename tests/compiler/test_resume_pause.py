import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_on_resume():
    code = """
def main_ui():
    on_resume(lambda: print("resumed"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ON_RESUME" in kotlin_code
    assert "LifecycleEventObserver" in kotlin_code


def test_on_pause():
    code = """
def main_ui():
    on_pause(lambda: print("paused"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ON_PAUSE" in kotlin_code
    assert "LifecycleEventObserver" in kotlin_code


def test_on_resume_and_pause():
    code = """
def main_ui():
    on_resume(lambda: print("start"))
    on_pause(lambda: print("stop"))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ON_RESUME" in kotlin_code
    assert "ON_PAUSE" in kotlin_code


def test_on_resume_with_state():
    code = """
def main_ui():
    count = state(0)
    on_resume(lambda: print(count))
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "ON_RESUME" in kotlin_code
