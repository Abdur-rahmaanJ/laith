from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from laith.compiler.frontend.symbols import Type, ANY_TYPE, VOID_TYPE

@dataclass
class IRValue:
    id: str
    type: Type

    def __repr__(self) -> str:
        return f"%{self.id}: {self.type}"

@dataclass(kw_only=True)
class IRInstruction:
    result: Optional[IRValue] = None
    
    def __repr__(self) -> str:
        res = f"{self.result} = " if self.result else ""
        return f"{res}{self.__class__.__name__.lower()}"

@dataclass(kw_only=True)
class Constant(IRInstruction):
    value: Any
    
    def __repr__(self) -> str:
        return f"{self.result} = const {self.value}"

@dataclass(kw_only=True)
class BinaryOp(IRInstruction):
    op: str
    left: IRValue
    right: IRValue
    
    def __repr__(self) -> str:
        return f"{self.result} = {self.op} {self.left.id} {self.right.id}"

@dataclass(kw_only=True)
class Call(IRInstruction):
    func_name: str
    args: List[IRValue]
    
    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        res = f"{self.result} = " if self.result else ""
        return f"{res}call {self.func_name}({args_str})"

@dataclass(kw_only=True)
class UICall(IRInstruction):
    func_name: str
    args: List[IRValue]
    body: Optional[IRBlock] = None
    keywords: Dict[str, Union[IRValue, IRBlock]] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        kws_str = ", ".join(f"{k}={v}" for k, v in self.keywords.items())
        all_args = ", ".join(filter(None, [args_str, kws_str]))
        body_str = f" {{\n  {self.body}\n}}" if self.body else ""
        return f"ui_call {self.func_name}({all_args}){body_str}"

@dataclass(kw_only=True)
class StateInit(IRInstruction):
    initial_value: IRValue
    
    def __repr__(self) -> str:
        return f"{self.result} = state_init({self.initial_value.id})"

@dataclass(kw_only=True)
class StateGet(IRInstruction):
    state_var: IRValue
    
    def __repr__(self) -> str:
        return f"{self.result} = state_get({self.state_var.id})"

@dataclass(kw_only=True)
class StateSet(IRInstruction):
    state_var: IRValue
    new_value: IRValue
    
    def __repr__(self) -> str:
        return f"state_set({self.state_var.id}, {self.new_value.id})"

@dataclass(kw_only=True)
class Return(IRInstruction):
    value: Optional[IRValue] = None
    
    def __repr__(self) -> str:
        return f"return {self.value.id if self.value else ''}"

@dataclass
class IRBlock:
    label: str
    instructions: List[IRInstruction] = field(default_factory=list)
    
    def add_instruction(self, inst: IRInstruction):
        self.instructions.append(inst)

    def __repr__(self) -> str:
        body = "\n  ".join(repr(i) for i in self.instructions)
        return f"{self.label}:\n  {body}"

@dataclass
class IRFunction:
    name: str
    return_type: Type
    args: List[IRValue]
    is_async: bool = False
    blocks: List[IRBlock] = field(default_factory=list)
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    
    def __repr__(self) -> str:
        decs = ""
        for d in self.decorators:
            args = ", ".join(f"{k}={v}" for k, v in d["args"].items())
            decs += f"@{d['name']}({args})\n"
        async_prefix = "async " if self.is_async else ""
        args_str = ", ".join(repr(a) for a in self.args)
        header = f"{decs}{async_prefix}def @{self.name}({args_str}) -> {self.return_type}:"
        body = "\n".join(repr(b) for b in self.blocks)
        return f"{header}\n{body}"

@dataclass
class IRModule:
    functions: List[IRFunction] = field(default_factory=list)
    
    def __repr__(self) -> str:
        return "\n\n".join(repr(f) for f in self.functions)
