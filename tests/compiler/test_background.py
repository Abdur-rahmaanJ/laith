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
    
    assert "class Sync_dataWorker" in kotlin_code
    assert "PeriodicWorkRequestBuilder<Sync_dataWorker>(1, TimeUnit.HOURS)" in kotlin_code
    assert ".setRequiredNetworkType(NetworkType.UNMETERED)" in kotlin_code
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
    
    assert "class TrackerService : LaithService()" in kotlin_code
    assert 'val channelId = "tracker_channel"' in kotlin_code
    assert '.setContentText("Running tracker")' in kotlin_code
    assert "NotificationCompat.Builder" in kotlin_code
