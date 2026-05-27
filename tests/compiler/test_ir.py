from tests.helpers.pool import IRArena
from laith.compiler.ir.nodes import IRValue, IRBlock, IRFunction, IRModule
from laith.compiler.ir.nodes import BinaryOp, Constant, Call, Return
from laith.compiler.frontend.symbols import INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE


class TestIRValueConstruction:
    def test_value_creation(self):
        v = IRValue(id="x", type=INT_TYPE)
        assert v.id == "x"
        assert v.type == INT_TYPE
        assert repr(v) == "%x: int"

    def test_value_equality(self):
        a = IRValue(id="a", type=INT_TYPE)
        b = IRValue(id="a", type=INT_TYPE)
        assert a == b

    def test_value_inequality(self):
        a = IRValue(id="a", type=INT_TYPE)
        b = IRValue(id="b", type=INT_TYPE)
        assert a != b


class TestIRBlockConstruction:
    def test_block_creation(self):
        block = IRBlock(label="entry")
        assert block.label == "entry"
        assert len(block.instructions) == 0

    def test_block_add_instruction(self):
        arena = IRArena()
        block = IRBlock(label="entry")
        r = arena.new_value(type=INT_TYPE)
        inst = arena.constant(42, type=INT_TYPE)
        block.add_instruction(inst)
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], Constant)

    def test_block_multiple_instructions(self):
        arena = IRArena()
        block = IRBlock(label="entry")
        c1 = arena.constant(1, type=INT_TYPE)
        c2 = arena.constant(2, type=INT_TYPE)
        r = arena.new_value(type=INT_TYPE)
        op = arena.new_instruction(
            BinaryOp, result=r, op="add",
            left=c1.result, right=c2.result,
        )
        block.add_instruction(c1)
        block.add_instruction(c2)
        block.add_instruction(op)
        assert len(block.instructions) == 3


class TestIRInstructionSemantics:
    def test_constant_no_side_effects(self):
        arena = IRArena()
        inst = arena.constant(42, type=INT_TYPE)
        assert inst.has_side_effects() is False
        assert inst.get_operands() == []

    def test_binary_op_no_side_effects(self):
        arena = IRArena()
        left = arena.new_value(type=INT_TYPE)
        right = arena.new_value(type=INT_TYPE)
        inst = arena.new_instruction(
            BinaryOp, result=arena.new_value(type=INT_TYPE),
            op="add", left=left, right=right,
        )
        assert inst.has_side_effects() is False
        assert inst.get_operands() == [left, right]

    def test_call_has_side_effects(self):
        arena = IRArena()
        arg = arena.new_value(type=INT_TYPE)
        inst = arena.new_instruction(
            Call, result=arena.new_value(type=VOID_TYPE),
            func_name="print", args=[arg],
        )
        assert inst.has_side_effects() is True
        assert inst.get_operands() == [arg]

    def test_return_has_side_effects(self):
        arena = IRArena()
        val = arena.new_value(type=INT_TYPE)
        inst = arena.new_instruction(Return, value=val)
        assert inst.has_side_effects() is True
        assert inst.get_operands() == [val]

    def test_return_no_value_operands(self):
        inst = Return(value=None)
        assert inst.get_operands() == []
        assert inst.has_side_effects() is True


class TestIRFunctionConstruction:
    def test_function_creation(self):
        func = IRFunction(name="f", return_type=INT_TYPE, args=[])
        assert func.name == "f"
        assert len(func.blocks) == 0

    def test_function_with_args(self):
        x = IRValue(id="x", type=INT_TYPE)
        func = IRFunction(name="add", return_type=INT_TYPE, args=[x])
        assert len(func.args) == 1
        assert func.args[0].id == "x"

    def test_function_with_block(self):
        arena = IRArena()
        block = IRBlock(label="entry")
        c = arena.constant(42, type=INT_TYPE)
        r = Return(value=c.result)
        block.add_instruction(c)
        block.add_instruction(r)
        func = IRFunction(name="f", return_type=INT_TYPE, args=[], blocks=[block])
        assert len(func.blocks) == 1
        assert len(func.blocks[0].instructions) == 2


class TestIRModuleConstruction:
    def test_empty_module(self):
        module = IRModule()
        assert len(module.functions) == 0
        assert len(module.classes) == 0

    def test_module_with_function(self):
        func = IRFunction(name="f", return_type=VOID_TYPE, args=[])
        module = IRModule(functions=[func])
        assert len(module.functions) == 1
        assert module.functions[0].name == "f"

    def test_module_multiple_functions(self):
        f1 = IRFunction(name="a", return_type=INT_TYPE, args=[])
        f2 = IRFunction(name="b", return_type=STR_TYPE, args=[])
        module = IRModule(functions=[f1, f2])
        assert len(module.functions) == 2
        names = {f.name for f in module.functions}
        assert names == {"a", "b"}
