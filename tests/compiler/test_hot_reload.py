import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.errors import CompileError


class TestHotReload:
    def test_basic_hot_reload(self, fresh_emitter):
        code = """
def main_ui():
    Text("Hello")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)

        # First emission
        kotlin1 = fresh_emitter.reset().emit(module)
        # Re-emission of same module should be identical
        kotlin2 = fresh_emitter.reset().emit(module)

        assert kotlin1 == kotlin2

    def test_incremental_module_change(self):
        code1 = """
def main_ui():
    Text("Hello")
"""
        code2 = """
def main_ui():
    Text("World")
"""
        tree1 = Parser.parse(code1)
        tree2 = Parser.parse(code2)
        analyzer = SemanticAnalyzer()

        scope1 = analyzer.analyze(tree1)
        module1 = IRBuilder(scope1).build(tree1)

        scope2 = analyzer.reset().analyze(tree2)
        module2 = IRBuilder(scope2).build(tree2)

        kotlin1 = KotlinEmitter().reset().emit(module1)
        kotlin2 = KotlinEmitter().reset().emit(module2)

        assert kotlin1 != kotlin2
        assert "Hello" in kotlin1
        assert "World" in kotlin2
