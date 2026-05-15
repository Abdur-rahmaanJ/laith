import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


def test_http_get():
    code = """
async def fetch():
    response = await http.get("https://api.example.com/data")
    return response.text
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "HttpURLConnection" in kotlin_code
    assert "GET" in kotlin_code
    assert "HttpResponse" in kotlin_code
    assert "Dispatchers.IO" in kotlin_code


def test_http_post():
    code = """
async def create():
    response = await http.post("https://api.example.com/data", json={"name": "test"})
    return response.status_code
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "POST" in kotlin_code
    assert "Content-Type" in kotlin_code
    assert "HttpResponse" in kotlin_code


def test_http_response_json():
    code = """
async def fetch():
    response = await http.get("https://api.example.com/data")
    data = response.json()
    return data
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "HttpResponse" in kotlin_code
    assert "JSONObject" in kotlin_code or "json()" in kotlin_code


def test_http_response_text():
    code = """
async def fetch():
    response = await http.get("https://api.example.com/data")
    text = response.text
    return text
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "HttpResponse" in kotlin_code


def test_http_response_status_code():
    code = """
async def fetch():
    response = await http.get("https://api.example.com/data")
    return response.status_code
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)

    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)

    assert "HttpResponse" in kotlin_code
