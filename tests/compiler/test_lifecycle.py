import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.errors import CompileError


class TestLifecycle:
    def test_on_resume(self, fresh_emitter):
        code = """
def main_ui():
    on_resume(lambda: print("resumed"))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "ON_RESUME" in kotlin
        assert "LifecycleEventObserver" in kotlin

    def test_on_pause(self, fresh_emitter):
        code = """
def main_ui():
    on_pause(lambda: print("paused"))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "ON_PAUSE" in kotlin
        assert "LifecycleEventObserver" in kotlin


class TestResumePause:
    def test_both_resume_pause(self, fresh_emitter):
        code = """
def main_ui():
    on_resume(lambda: print("resumed"))
    on_pause(lambda: print("paused"))
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        non_import_lines = [l for l in kotlin.split("\n") if not l.startswith("import ")]
        count = sum(line.count("LifecycleEventObserver") for line in non_import_lines)
        assert count == 2  # One for resume, one for pause
