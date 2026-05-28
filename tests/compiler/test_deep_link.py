import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestDeepLink:
    def test_route_with_scheme_generates_deep_link(self, fresh_emitter):
        code = """
@route(path="/profile/{userId}", scheme="laithapp")
def profile():
    pass

def main_ui():
    Navigator.push(profile)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        emitter = fresh_emitter.reset()
        kotlin = emitter.emit(module)

        assert "navDeepLink" in kotlin
        assert 'uriPattern = "laithapp://laith.app/profile/{userId}"' in kotlin
        assert "deepLinks = listOf(navDeepLink" in kotlin

    def test_route_without_scheme_no_deep_link(self, fresh_emitter):
        code = """
@route(path="/home")
def home():
    pass

def main_ui():
    Navigator.push(home)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        emitter = fresh_emitter.reset()
        kotlin = emitter.emit(module)

        assert "navDeepLink" not in kotlin

    def test_route_with_custom_host(self, fresh_emitter):
        code = """
@route(path="/items", scheme="https", host="example.com")
def items():
    pass

def main_ui():
    Navigator.push(items)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        emitter = fresh_emitter.reset()
        kotlin = emitter.emit(module)

        assert "uriPattern = \"https://example.com/items\"" in kotlin

    def test_get_deep_link_routes(self, fresh_emitter):
        code = """
@route(path="/a", scheme="app")
def a():
    pass

@route(path="/b", scheme="https", host="x.com")
def b():
    pass

@route(path="/c")
def c():
    pass

def main_ui():
    Navigator.push(a)
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        emitter = fresh_emitter.reset()
        emitter.emit(module)

        links = emitter.get_deep_link_routes()
        assert len(links) == 2
        assert links[0]["scheme"] == "app"
        assert links[0]["host"] == "laith.app"
        assert links[0]["path"] == "/a"
        assert links[1]["scheme"] == "https"
        assert links[1]["host"] == "x.com"
        assert links[1]["path"] == "/b"
