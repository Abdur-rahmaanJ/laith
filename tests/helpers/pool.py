from __future__ import annotations
from typing import List, Optional, Type, Dict
from laith.compiler.ir.nodes import (
    IRValue, IRInstruction, IRBlock, IRFunction, IRModule,
    Constant, BinaryOp, Call, Return, IRIf, TryExcept, Raise,
    ClassInit, AttributeGet, AttributeSet, MethodCall,
    StateInit, StateGet, StateSet,
    UICall, NavigatorPush, NavigatorPop,
    Jump, Branch, IRClass, IRField, IRMethod,
    ChannelInit, ChannelSend, ChannelCollect,
    ServiceStart, ServiceStop,
)
from laith.compiler.frontend.symbols import Type, INT_TYPE, STR_TYPE, BOOL_TYPE, VOID_TYPE, ANY_TYPE


class IRPool:
    __slots__ = ("_int_val", "_str_val", "_bool_val", "_void_val", "_any_val")

    def __init__(self):
        self._int_val = IRValue(id="0", type=INT_TYPE)
        self._str_val = IRValue(id="1", type=STR_TYPE)
        self._bool_val = IRValue(id="2", type=BOOL_TYPE)
        self._void_val = IRValue(id="3", type=VOID_TYPE)
        self._any_val = IRValue(id="4", type=ANY_TYPE)

    def value(self, id: str, type: Type) -> IRValue:
        return IRValue(id=id, type=type)

    def typed(self, type: Type) -> IRValue:
        mapping = {
            INT_TYPE: self._int_val,
            STR_TYPE: self._str_val,
            BOOL_TYPE: self._bool_val,
            VOID_TYPE: self._void_val,
            ANY_TYPE: self._any_val,
        }
        return mapping.get(type, self._any_val)

    @property
    def int_val(self) -> IRValue:
        return self._int_val

    @property
    def str_val(self) -> IRValue:
        return self._str_val

    @property
    def bool_val(self) -> IRValue:
        return self._bool_val

    @property
    def void_val(self) -> IRValue:
        return self._void_val

    @property
    def any_val(self) -> IRValue:
        return self._any_val


class IRArena:
    def __init__(self):
        self._values: List[IRValue] = []
        self._instructions: List[IRInstruction] = []
        self._blocks: List[IRBlock] = []
        self._counter: int = 0

    def new_value(self, id: Optional[str] = None, type: Type = ANY_TYPE) -> IRValue:
        if id is None:
            id = str(self._counter)
            self._counter += 1
        v = IRValue(id=id, type=type)
        self._values.append(v)
        return v

    def new_instruction(self, cls: Type[IRInstruction], **kwargs) -> IRInstruction:
        inst = cls(**kwargs)
        self._instructions.append(inst)
        return inst

    def new_block(self, label: str) -> IRBlock:
        b = IRBlock(label=label)
        self._blocks.append(b)
        return b

    @property
    def int_val(self) -> IRValue:
        return self.new_value(type=INT_TYPE)

    @property
    def str_val(self) -> IRValue:
        return self.new_value(type=STR_TYPE)

    @property
    def bool_val(self) -> IRValue:
        return self.new_value(type=BOOL_TYPE)

    @property
    def void_val(self) -> IRValue:
        return self.new_value(type=VOID_TYPE)

    def reset(self):
        self._values.clear()
        self._instructions.clear()
        self._blocks.clear()
        self._counter = 0

    def constant(self, value, type: Optional[Type] = None, result_id: Optional[str] = None) -> Constant:
        if type is None:
            if isinstance(value, int):
                type = INT_TYPE
            elif isinstance(value, str):
                type = STR_TYPE
            elif isinstance(value, bool):
                type = BOOL_TYPE
            else:
                type = ANY_TYPE
        r = self.new_value(id=result_id, type=type)
        inst = self.new_instruction(Constant, result=r, value=value)
        return inst

    def binary_op(self, op: str, left: IRValue, right: IRValue, result_type: Type = ANY_TYPE) -> BinaryOp:
        r = self.new_value(type=result_type)
        inst = self.new_instruction(BinaryOp, result=r, op=op, left=left, right=right)
        return inst

    def call(self, func_name: str, args: List[IRValue], result_type: Type = ANY_TYPE) -> Call:
        r = self.new_value(type=result_type)
        inst = self.new_instruction(Call, result=r, func_name=func_name, args=args)
        return inst

    def return_(self, value: Optional[IRValue] = None) -> Return:
        inst = self.new_instruction(Return, value=value)
        return inst
