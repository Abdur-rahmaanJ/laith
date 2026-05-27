from __future__ import annotations
import hashlib
from laith.compiler.ir.nodes import (
    IRModule, IRFunction, IRBlock, IRInstruction,
    Constant, BinaryOp, Call, Return, IRValue,
)


def structural_hash(module: IRModule) -> str:
    h = hashlib.sha256()

    for func in sorted(module.functions, key=lambda f: f.name):
        h.update(func.name.encode())
        h.update(str(len(func.args)).encode())
        for block in sorted(func.blocks, key=lambda b: b.label):
            for inst in block.instructions:
                h.update(_instruction_fingerprint(inst).encode())

    return h.hexdigest()


def _instruction_fingerprint(inst: IRInstruction) -> str:
    if isinstance(inst, Constant):
        return f"const({inst.value!r})"
    if isinstance(inst, BinaryOp):
        return f"binop({inst.op})"
    if isinstance(inst, Call):
        return f"call({inst.func_name},{len(inst.args)})"
    if isinstance(inst, Return):
        return f"return({inst.value is not None})"
    return inst.__class__.__name__
