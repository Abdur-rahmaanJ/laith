import pytest
from laith.compiler.frontend.analyzer import SemanticAnalyzer, Parser
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.ir.nodes import Constant, BinaryOp
from laith.compiler.optimizer.base import Optimizer
from laith.compiler.optimizer.dce import DCEPass
from laith.compiler.optimizer.const_fold import ConstantFoldingPass

def test_dce_simple():
    code = """
def dead_code():
    x = 10
    y = 20
    z = x + 5
    return x
"""
    # y and z are dead.
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    # Before optimization
    func = module.functions[0]
    # Constant(10), Constant(20), Constant(5), BinaryOp(x+5), Return(x)
    # Actually, Assignment might create more instructions
    
    optimizer = Optimizer()
    optimizer.add_pass(DCEPass())
    optimizer.optimize(module)
    
    # After optimization, y=20 and z=x+5 (and its const 5) should be gone.
    # We should only have x=10 and return x.
    
    func = next(f for f in module.functions if f.name == "dead_code")
    insts = func.blocks[0].instructions
    print(f"\nOptimized IR:\n{module}")
    inst_names = [type(i).__name__ for i in insts]
    
    # Expected: Constant(10), Return(x)
    assert not any(isinstance(i, BinaryOp) for i in insts)
    # The '20' constant should also be gone
    consts = [i.value for i in insts if isinstance(i, Constant)]
    assert 20 not in consts
    assert 10 in consts

def test_dce_side_effects():
    code = """
def side_effects():
    x = 10
    print("Alive")
    return x
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    optimizer = Optimizer()
    optimizer.add_pass(DCEPass())
    optimizer.optimize(module)
    
    print(f"\nOptimized IR (side effects):\n{module}")
    func = next(f for f in module.functions if f.name == "side_effects")
    insts = func.blocks[0].instructions
    inst_names = [type(i).__name__ for i in insts]
    
    assert "Call" in inst_names # print() has side effects
    assert "Return" in inst_names

def test_constant_folding():
    code = """
def fold():
    x = 1 + 2
    return x
"""
    tree = Parser.parse(code)
    analyzer = SemanticAnalyzer()
    global_scope = analyzer.analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    
    optimizer = Optimizer()
    optimizer.add_pass(ConstantFoldingPass())
    optimizer.add_pass(DCEPass())
    optimizer.optimize(module)
    
    func = next(f for f in module.functions if f.name == "fold")
    insts = func.blocks[0].instructions
    print(f"\nOptimized IR (folding):\n{module}")
    
    # Should be Constant(3) and Return
    assert not any(isinstance(i, BinaryOp) for i in insts)
    consts = [i.value for i in insts if isinstance(i, Constant)]
    assert 3 in consts
    assert 1 not in consts
    assert 2 not in consts
