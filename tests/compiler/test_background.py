import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestBackground:
    def test_periodic_task(self, fresh_emitter):
        code = """
@periodic_task(interval="1h", requires_wifi=True)
async def sync_data():
    print("Syncing...")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "suspend fun syncData" in kotlin
        assert "fun scheduleLaithTasks" in kotlin

    def test_foreground_service(self, fresh_emitter):
        code = """
@foreground_service(notification="Running tracker")
async def tracker():
    print("Tracking...")
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "suspend fun tracker" in kotlin
        assert "fun scheduleLaithTasks" in kotlin
