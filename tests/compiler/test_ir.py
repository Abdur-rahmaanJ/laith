import pytest
import ast
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.ir.nodes import BinaryOp, Constant, Return

def test_ir_generation_simple():
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
    
    # +1 for global_init
    assert len(module.functions) == 2
    func = next(f for f in module.functions if f.name == "add_numbers")
    assert func.name == "add_numbers"
    assert len(func.blocks) == 1
    block = func.blocks[0]
    
    # Check instructions
    # 1. BinaryOp (a + b)
    # 2. Return (result)
    assert len(block.instructions) == 2
    assert isinstance(block.instructions[0], BinaryOp)
    assert block.instructions[0].op == "add"
    assert isinstance(block.instructions[1], Return)

def test_ir_complex_expression():
    code = """
def compute(x: int) -> int:
    y = x * 2 + 10
    return y
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    func = next(f for f in module.functions if f.name == "compute")
    block = func.blocks[0]
    # 1. Constant (2)
    # 2. BinaryOp (x * 2)
    # 3. Constant (10)
    # 4. BinaryOp (result_of_mul + 10)
    # 5. Return (y)
    assert len(block.instructions) == 5
    assert isinstance(block.instructions[0], Constant)
    assert block.instructions[0].value == 2
    assert isinstance(block.instructions[1], BinaryOp)
    assert block.instructions[1].op == "mul"
    assert isinstance(block.instructions[2], Constant)
    assert block.instructions[2].value == 10
    assert isinstance(block.instructions[3], BinaryOp)
    assert block.instructions[3].op == "add"
    assert isinstance(block.instructions[4], Return)
