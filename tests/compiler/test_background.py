import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter

def test_kotlin_emission_periodic_task():
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
    
    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)
    
    assert "suspend fun syncData" in kotlin_code
    assert "fun scheduleLaithTasks" in kotlin_code
    assert "fun scheduleLaithTasks(context: Context)" in kotlin_code

def test_kotlin_emission_foreground_service():
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
    
    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)
    
    assert "suspend fun tracker" in kotlin_code
    assert "fun scheduleLaithTasks" in kotlin_code
