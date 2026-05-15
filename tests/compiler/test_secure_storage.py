import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_secure_storage_init():
    code = """
def main_ui():
    storage = SecureStorage("secrets")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "SecureStorageUtil" in kotlin_code


def test_secure_storage_get():
    code = """
def main_ui():
    storage = SecureStorage("secrets")
    token = storage.get("token")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "getString" in kotlin_code
    assert "token" in kotlin_code


def test_secure_storage_set():
    code = """
def main_ui():
    storage = SecureStorage("secrets")
    storage.set("token", "abc123")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "putString" in kotlin_code


def test_secure_storage_remove():
    code = """
def main_ui():
    storage = SecureStorage("secrets")
    storage.remove("token")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert ".remove" in kotlin_code or "remove(" in kotlin_code


def test_secure_storage_contains():
    code = """
def main_ui():
    storage = SecureStorage("secrets")
    has = storage.contains("token")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "contains" in kotlin_code
