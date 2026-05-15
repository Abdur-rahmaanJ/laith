import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_database_init():
    code = """
def main_ui():
    db = Database("app.db")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "openOrCreateDatabase" in kotlin_code
    assert "app.db" in kotlin_code


def test_database_query():
    code = """
def main_ui():
    db = Database("app.db")
    users = db.query("SELECT * FROM users")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "rawQuery" in kotlin_code
    assert "SELECT * FROM users" in kotlin_code


def test_database_execute():
    code = """
def main_ui():
    db = Database("app.db")
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "execSQL" in kotlin_code
    assert "CREATE TABLE" in kotlin_code


def test_database_execute_with_params():
    code = """
def main_ui():
    db = Database("app.db")
    db.execute("INSERT INTO users (name) VALUES (?)", "Alice")
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "execSQL" in kotlin_code
    assert "Alice" in kotlin_code


def test_database_query_with_params():
    code = """
def main_ui():
    db = Database("app.db")
    uid = 1
    user = db.query("SELECT * FROM users WHERE id = ?", uid)
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "rawQuery" in kotlin_code
    assert "arrayOf" in kotlin_code


def test_database_close():
    code = """
def main_ui():
    db = Database("app.db")
    db.close()
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert ".close()" in kotlin_code
