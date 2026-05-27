from tests.helpers.pool import IRArena
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRValue,
    Constant, BinaryOp, Call, Return,
)
from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE
from laith.compiler.optimizer.base import Optimizer
from laith.compiler.optimizer.dce import DCEPass
from laith.compiler.optimizer.const_fold import ConstantFoldingPass
from laith.compiler.optimizer.inliner import InlinerPass
from tests.helpers.ir_assert import assert_ir_equal, assert_ir_not_equal

import copy


def _make_simple_module(arena: IRArena, instructions: list) -> IRModule:
    block = IRBlock(label="entry")
    for inst in instructions:
        block.add_instruction(inst)
    func = IRFunction(name="f", return_type=INT_TYPE, args=[], blocks=[block])
    return IRModule(functions=[func])


class TestConstantFolding:
    def test_fold_add(self, ir_arena):
        left = ir_arena.new_value(type=INT_TYPE)
        right = ir_arena.new_value(type=INT_TYPE)
        c1 = ir_arena.constant(1, type=INT_TYPE)
        c2 = ir_arena.constant(2, type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        op = ir_arena.new_instruction(BinaryOp, result=r, op="add", left=c1.result, right=c2.result)
        ret = ir_arena.new_instruction(Return, value=r)

        module = _make_simple_module(ir_arena, [c1, c2, op, ret])
        fold = ConstantFoldingPass()
        changed = fold.run(module)

        assert changed is True
        folded = module.functions[0].blocks[0].instructions
        # The BinaryOp should be replaced with a Constant(3)
        constants = [i for i in folded if isinstance(i, Constant)]
        binary_ops = [i for i in folded if isinstance(i, BinaryOp)]
        assert len(binary_ops) == 0
        assert any(c.value == 3 for c in constants)

    def test_fold_mul(self, ir_arena):
        c1 = ir_arena.constant(6, type=INT_TYPE)
        c2 = ir_arena.constant(7, type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        op = ir_arena.new_instruction(BinaryOp, result=r, op="mul", left=c1.result, right=c2.result)
        ret = ir_arena.new_instruction(Return, value=r)

        module = _make_simple_module(ir_arena, [c1, c2, op, ret])
        fold = ConstantFoldingPass()
        changed = fold.run(module)

        assert changed is True
        constants = [i for i in module.functions[0].blocks[0].instructions if isinstance(i, Constant)]
        assert any(c.value == 42 for c in constants)

    def test_no_fold_when_not_constant(self, ir_arena):
        x = ir_arena.new_value(id="x", type=INT_TYPE)
        y = ir_arena.new_value(id="y", type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        op = ir_arena.new_instruction(BinaryOp, result=r, op="add", left=x, right=y)
        ret = ir_arena.new_instruction(Return, value=r)

        module = _make_simple_module(ir_arena, [op, ret])
        fold = ConstantFoldingPass()
        changed = fold.run(module)

        assert changed is False
        insts = module.functions[0].blocks[0].instructions
        assert any(isinstance(i, BinaryOp) for i in insts)

    def test_fold_idempotent(self, ir_arena):
        c1 = ir_arena.constant(5, type=INT_TYPE)
        c2 = ir_arena.constant(3, type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        op = ir_arena.new_instruction(BinaryOp, result=r, op="sub", left=c1.result, right=c2.result)
        ret = ir_arena.new_instruction(Return, value=r)

        module = _make_simple_module(ir_arena, [c1, c2, op, ret])
        fold = ConstantFoldingPass()

        fold.run(module)
        changed2 = fold.run(module)

        assert changed2 is False


class TestDCE:
    def test_remove_dead_code(self, ir_arena):
        c1 = ir_arena.constant(10, type=INT_TYPE)
        c2 = ir_arena.constant(20, type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        op = ir_arena.new_instruction(BinaryOp, result=r, op="add", left=c1.result, right=c2.result)
        ret = ir_arena.new_instruction(Return, value=ir_arena.int_val)

        # BinaryOp result (%r) is never used → dead
        # Constants c1/c2 are operands of BinaryOp → not dead in single-pass DCE
        module = _make_simple_module(ir_arena, [c1, c2, op, ret])
        dce = DCEPass()
        changed = dce.run(module)

        assert changed is True
        insts = module.functions[0].blocks[0].instructions
        # Only BinaryOp should be removed (its result is unused)
        assert not any(isinstance(i, BinaryOp) for i in insts)

    def test_keep_live_code(self, ir_arena):
        c = ir_arena.constant(42, type=INT_TYPE)
        ret = ir_arena.new_instruction(Return, value=c.result)

        module = _make_simple_module(ir_arena, [c, ret])
        dce = DCEPass()
        changed = dce.run(module)

        assert changed is False
        assert len(module.functions[0].blocks[0].instructions) == 2

    def test_keep_side_effects(self, ir_arena):
        arg = ir_arena.new_value(type=INT_TYPE)
        call = ir_arena.new_instruction(Call, result=ir_arena.new_value(type=VOID_TYPE), func_name="print", args=[arg])
        ret = ir_arena.new_instruction(Return)

        module = _make_simple_module(ir_arena, [call, ret])
        dce = DCEPass()
        changed = dce.run(module)

        assert changed is False
        assert any(isinstance(i, Call) for i in module.functions[0].blocks[0].instructions)

    def test_dce_idempotent(self, ir_arena):
        c = ir_arena.constant(10, type=INT_TYPE)
        dead = ir_arena.constant(99, type=INT_TYPE)  # unused
        ret = ir_arena.new_instruction(Return, value=c.result)

        module = _make_simple_module(ir_arena, [c, dead, ret])
        dce = DCEPass()
        dce.run(module)
        changed2 = dce.run(module)

        assert changed2 is False


class TestOptimizerComposition:
    def test_fold_then_dce(self, ir_arena):
        c1 = ir_arena.constant(2, type=INT_TYPE)
        c2 = ir_arena.constant(3, type=INT_TYPE)
        r1 = ir_arena.new_value(type=INT_TYPE)
        add = ir_arena.new_instruction(BinaryOp, result=r1, op="add", left=c1.result, right=c2.result)
        r2 = ir_arena.new_value(type=INT_TYPE)
        one = ir_arena.constant(1, type=INT_TYPE)
        mul = ir_arena.new_instruction(BinaryOp, result=r2, op="mul", left=r1, right=one.result)
        ret = ir_arena.new_instruction(Return, value=r2)

        module = _make_simple_module(ir_arena, [one, c1, c2, add, mul, ret])

        optimizer = Optimizer()
        optimizer.add_pass(ConstantFoldingPass())
        optimizer.add_pass(DCEPass())
        optimizer.optimize(module)

        insts = module.functions[0].blocks[0].instructions
        # After fold + DCE: all operations should be folded to constants
        assert not any(isinstance(i, BinaryOp) for i in insts)


class TestInliner:
    def test_inline_simple(self, ir_arena):
        # Create a small callee function: def double(x): return x * 2
        x = ir_arena.new_value(id="x", type=INT_TYPE)
        c2 = ir_arena.constant(2, type=INT_TYPE)
        r = ir_arena.new_value(type=INT_TYPE)
        mul = ir_arena.new_instruction(BinaryOp, result=r, op="mul", left=x, right=c2.result)
        ret = ir_arena.new_instruction(Return, value=r)
        body = IRBlock(label="entry")
        body.add_instruction(c2)
        body.add_instruction(mul)
        body.add_instruction(ret)
        callee = IRFunction(name="double", return_type=INT_TYPE, args=[x], blocks=[body])

        # Create caller: def main(): return double(5)
        arg = ir_arena.constant(5, type=INT_TYPE)
        call_r = ir_arena.new_value(type=INT_TYPE)
        call = ir_arena.new_instruction(Call, result=call_r, func_name="double", args=[arg.result])
        main_ret = ir_arena.new_instruction(Return, value=call_r)
        main_body = IRBlock(label="entry")
        main_body.add_instruction(arg)
        main_body.add_instruction(call)
        main_body.add_instruction(main_ret)
        main_func = IRFunction(name="main", return_type=INT_TYPE, args=[], blocks=[main_body])

        module = IRModule(functions=[callee, main_func])
        inliner = InlinerPass(threshold=10)
        changed = inliner.run(module)

        assert changed is True
        main = next(f for f in module.functions if f.name == "main")
        call_insts = [i for i in main.blocks[0].instructions if isinstance(i, Call) and i.func_name == "double"]
        assert len(call_insts) == 0  # Call should be inlined away
