import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter

def test_kotlin_emission_simple():
    code = """
def add_numbers(a: int, b: int) -> int:
    result = a + b
    return result
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)
    
    # Expected output (modulo exact spacing/newlines):
    # fun add_numbers(v_a: Int, v_b: Int): Int {
    #     val v_0 = v_a + v_b
    #     return v_0
    # }
    
    assert "fun add_numbers(v_a: Int, v_b: Int): Int {" in kotlin_code
    assert "val v_0 = v_a + v_b" in kotlin_code
    assert "return v_0" in kotlin_code

def test_kotlin_emission_async():
    code = """
async def fetch() -> str:
    return "done"
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    emitter = KotlinEmitter()
    kotlin_code = emitter.emit(module)
    
    assert "suspend fun fetch(): String {" in kotlin_code
    assert 'val v_0 = "done"' in kotlin_code
    assert "return v_0" in kotlin_code
