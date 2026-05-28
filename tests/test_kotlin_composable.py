import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from laith.utils.config import AppConfig
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestKotlinComposable:
    def emit(self, code: str) -> str:
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        emitter = KotlinEmitter()
        return emitter.emit(module)

    def test_basic_kotlin_composable(self):
        code = """
def main_ui():
    KotlinComposable("com.example.MyScreen")
"""
        kotlin = self.emit(code)
        assert "com.example.MyScreen()" in kotlin or "com.example.MyScreen(" in kotlin

    def test_kotlin_composable_with_kwargs(self):
        code = """
def main_ui():
    KotlinComposable("com.example.MyScreen", title="Hello", count=42)
"""
        kotlin = self.emit(code)
        assert "com.example.MyScreen(" in kotlin
        assert "title =" in kotlin
        assert "count =" in kotlin

    def test_kotlin_composable_snake_to_camel(self):
        code = """
def main_ui():
    KotlinComposable("com.example.MyScreen", on_click=lambda: None)
"""
        kotlin = self.emit(code)
        assert "com.example.MyScreen(" in kotlin
        assert "onClick =" in kotlin

    def test_kotlin_composable_in_column(self):
        code = """
def main_ui():
    Column(
        KotlinComposable("com.example.MyScreen")
    )
"""
        kotlin = self.emit(code)
        assert "com.example.MyScreen()" in kotlin or "com.example.MyScreen(" in kotlin
        assert "Column" in kotlin

    def test_kotlin_composable_with_multiple_args(self):
        code = """
def main_ui():
    KotlinComposable("com.example.Greeting", name="World", age=25, enabled=True)
"""
        kotlin = self.emit(code)
        assert "com.example.Greeting(" in kotlin
        assert "name =" in kotlin
        assert "age =" in kotlin
        assert "enabled =" in kotlin

    def test_is_composable(self):
        code = """
def main_ui():
    KotlinComposable("com.example.MyScreen")
"""
        kotlin = self.emit(code)
        assert "@Composable" in kotlin
