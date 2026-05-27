from __future__ import annotations
import pytest
from hypothesis import given, strategies as st, settings
from laith.compiler.ir.nodes import IRValue, IRBlock, Constant, BinaryOp, Call, Return, IRFunction, IRModule
from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE


# Hypothesis strategies for IR nodes
@st.composite
def ir_value_id(draw):
    return draw(st.text(min_size=1, max_size=8, alphabet="abcdefghijklmnopqrstuvwxyz_"))


@st.composite
def ir_type(draw):
    return draw(st.sampled_from([INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE]))


@st.composite
def ir_value(draw):
    return IRValue(
        id=draw(ir_value_id()),
        type=draw(ir_type()),
    )


@st.composite
def constant_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.text(min_size=0, max_size=10),
        st.booleans(),
    ))


class TestIRInvariants:
    @given(ir_value(), ir_value())
    @settings(max_examples=50)
    def test_binary_op_accepts_any_values(self, left, right):
        r = IRValue(id="r", type=left.type)
        inst = BinaryOp(result=r, op="add", left=left, right=right)
        assert inst.get_operands() == [left, right]
        assert inst.has_side_effects() is False

    @given(ir_value())
    @settings(max_examples=50)
    def test_call_always_has_side_effects(self, arg):
        r = IRValue(id="r", type=VOID_TYPE)
        inst = Call(result=r, func_name="print", args=[arg])
        assert inst.has_side_effects() is True

    @given(constant_value())
    @settings(max_examples=50)
    def test_constant_no_operands(self, val):
        r = IRValue(id="r", type=ANY_TYPE)
        inst = Constant(result=r, value=val)
        assert inst.get_operands() == []
        assert inst.has_side_effects() is False

    def test_return_always_has_side_effects(self):
        inst = Return(value=None)
        assert inst.has_side_effects() is True

    def test_empty_block_has_no_instructions(self):
        block = IRBlock(label="entry")
        assert len(block.instructions) == 0

    def test_empty_module_has_no_functions(self):
        module = IRModule()
        assert len(module.functions) == 0
        assert len(module.classes) == 0
