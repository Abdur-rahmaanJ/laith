import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_resource_basic():
    code = """
async def fetch_data() -> str:
    return "data"

def main_ui():
    data = resource(fetch_data)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Resource" in kotlin_code
    assert "loading" in kotlin_code
    assert "error" in kotlin_code


def test_resource_data_access():
    code = """
async def fetch_data() -> str:
    return "data"

def main_ui():
    data = resource(fetch_data)
    value = data.data
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "Resource" in kotlin_code
    assert ".data" in kotlin_code


def test_resource_loading_access():
    code = """
async def fetch_data() -> str:
    return "data"

def main_ui():
    data = resource(fetch_data)
    is_loading = data.loading
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert ".loading" in kotlin_code


def test_resource_retry():
    code = """
async def fetch_data() -> str:
    return "data"

def main_ui():
    data = resource(fetch_data)
    data.retry()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "retry()" in kotlin_code


def test_resource_cancel():
    code = """
async def fetch_data() -> str:
    return "data"

def main_ui():
    data = resource(fetch_data)
    data.cancel()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "cancel()" in kotlin_code
