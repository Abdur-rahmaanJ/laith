import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_requires_permission_decorator():
    code = """
@requires_permission("CAMERA")
def open_camera():
    print("opened")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)

    assert "android.permission.CAMERA" in global_scope.metadata["required_permissions"]


def test_requires_permission_decorator_kotlin():
    code = """
@requires_permission("CAMERA")
def open_camera():
    print("opened")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "checkSelfPermission" in kotlin_code
    assert "CAMERA" in kotlin_code


def test_requires_permission_location():
    code = """
@requires_permission("ACCESS_FINE_LOCATION")
def get_gps():
    print("locating")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)

    assert "android.permission.ACCESS_FINE_LOCATION" in global_scope.metadata["required_permissions"]


def test_remember_permission():
    code = """
def main_ui():
    cam = remember_permission("CAMERA")
    if cam:
        Text("Granted")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "remember" in kotlin_code
    assert "checkSelfPermission" in kotlin_code


def test_remember_permission_check():
    code = """
def main_ui():
    cam = remember_permission("CAMERA")
    if cam:
        Button("Open Camera", on_click=lambda: print("open"))
    else:
        Text("No permission")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "checkSelfPermission" in kotlin_code
    assert "Button" in kotlin_code
