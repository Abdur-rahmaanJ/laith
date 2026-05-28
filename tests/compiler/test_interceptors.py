import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestInterceptors:
    def test_emits_interceptor_lists(self, fresh_emitter):
        code = """
def add_auth(headers):
    return headers

def main_ui():
    http.add_request_interceptor(add_auth)
    resp = http.get("https://example.com")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "requestInterceptors" in kotlin
        assert "responseInterceptors" in kotlin
        assert "addRequestInterceptor" in kotlin
        assert "addResponseInterceptor" in kotlin

    def test_request_interceptor_callable_reference(self, fresh_emitter):
        code = """
def add_auth(headers):
    headers["Authorization"] = "Bearer token"
    return headers

def main_ui():
    http.add_request_interceptor(add_auth)
    resp = http.get("https://example.com")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "addRequestInterceptor" in kotlin
        assert "::addAuth" in kotlin

    def test_response_interceptor_callable_reference(self, fresh_emitter):
        code = """
def log_response(resp):
    print(resp.status_code)
    return resp

def main_ui():
    http.add_response_interceptor(log_response)
    resp = http.get("https://example.com")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "addResponseInterceptor" in kotlin
        assert "::logResponse" in kotlin

    def test_interceptors_apply_to_http_call(self, fresh_emitter):
        code = """
def auth(headers):
    return headers

def main_ui():
    http.add_request_interceptor(auth)
    resp = http.get("https://example.com")
    Text(resp.text)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "for (interceptor in requestInterceptors)" in kotlin
        assert "for (interceptor in responseInterceptors)" in kotlin
        assert "conn.setRequestProperty" in kotlin
