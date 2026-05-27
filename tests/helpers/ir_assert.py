from __future__ import annotations
from typing import List
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction,
    Constant, BinaryOp, Call, Return, IRValue,
)


def assert_ir_equal(actual: IRModule, expected: IRModule):
    _compare_modules(actual, expected)


def assert_ir_not_equal(actual: IRModule, expected: IRModule):
    try:
        _compare_modules(actual, expected)
    except AssertionError:
        return
    raise AssertionError("IR modules are equal but expected them to differ")


def _compare_modules(a: IRModule, b: IRModule):
    a_funcs = sorted(a.functions, key=lambda f: f.name)
    b_funcs = sorted(b.functions, key=lambda f: f.name)
    assert len(a_funcs) == len(b_funcs), (
        f"Function count mismatch: {len(a_funcs)} vs {len(b_funcs)}"
    )
    for af, bf in zip(a_funcs, b_funcs):
        assert af.name == bf.name, f"Function name: {af.name} vs {bf.name}"
        assert len(af.args) == len(bf.args), (
            f"Arg count in {af.name}: {len(af.args)} vs {len(bf.args)}"
        )
        _compare_blocks(af.blocks, bf.blocks, context=f"function {af.name}")


def _compare_blocks(a: List[IRBlock], b: List[IRBlock], context: str = ""):
    assert len(a) == len(b), (
        f"Block count mismatch in {context}: {len(a)} vs {len(b)}"
    )
    for ab, bb in zip(a, b):
        _compare_instructions(ab.instructions, bb.instructions, context=f"{context} block {ab.label}")


def _compare_instructions(a: List[IRInstruction], b: List[IRInstruction], context: str = ""):
    assert len(a) == len(b), (
        f"Instruction count mismatch in {context}: {len(a)} vs {len(b)}"
    )
    for i, (ai, bi) in enumerate(zip(a, b)):
        assert type(ai) is type(bi), (
            f"Instruction {i} type mismatch in {context}: {type(ai).__name__} vs {type(bi).__name__}"
        )
        assert ai.has_side_effects() == bi.has_side_effects(), (
            f"Instruction {i} side-effect mismatch in {context}"
        )
        _compare_instruction_content(ai, bi, i, context)


def _compare_instruction_content(ai: IRInstruction, bi: IRInstruction, idx: int, context: str):
    if isinstance(ai, Constant):
        assert ai.value == bi.value, (
            f"Instruction {idx} constant value mismatch in {context}: {ai.value!r} vs {bi.value!r}"
        )
    elif isinstance(ai, BinaryOp):
        assert ai.op == bi.op, (
            f"Instruction {idx} binary op mismatch in {context}: {ai.op} vs {bi.op}"
        )
    elif isinstance(ai, Call):
        assert ai.func_name == bi.func_name, (
            f"Instruction {idx} call target mismatch in {context}: {ai.func_name} vs {bi.func_name}"
        )
        assert len(ai.args) == len(bi.args), (
            f"Instruction {idx} arg count mismatch in {context}: {len(ai.args)} vs {len(bi.args)}"
        )
    elif isinstance(ai, Return):
        assert (ai.value is None) == (bi.value is None), (
            f"Instruction {idx} return value presence mismatch in {context}"
        )
