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

@dataclass
class IRField:
    name: str
    type: Type

@dataclass
class IRMethod:
    name: str
    return_type: Type
    args: List[IRValue]
    is_async: bool = False
    blocks: List[IRBlock] = field(default_factory=list)
    decorators: List[Dict[str, Any]] = field(default_factory=list)
    is_constructor: bool = False

    def __repr__(self) -> str:
        decs = ""
        for d in self.decorators:
            args = ", ".join(f"{k}={v}" for k, v in d["args"].items())
            decs += f"@{d['name']}({args})\n"
        async_prefix = "async " if self.is_async else ""
        args_str = ", ".join(repr(a) for a in self.args)
        header = f"{decs}{async_prefix}method @{self.name}({args_str}) -> {self.return_type}:"
        body = "\n".join(repr(b) for b in self.blocks)
        return f"{header}\n{body}"

@dataclass
class IRClass:
    name: str
    fields: List[IRField] = field(default_factory=list)
    methods: List[IRMethod] = field(default_factory=list)
    decorators: List[Dict[str, Any]] = field(default_factory=list)

    def __repr__(self) -> str:
        fields_str = "\n  ".join(f"field {f.name}: {f.type}" for f in self.fields)
        methods_str = "\n\n".join(repr(m) for m in self.methods)
        return f"class {self.name} {{\n  {fields_str}\n\n{methods_str}\n}}"

@dataclass(kw_only=True)
class IRInstruction:
    result: Optional[IRValue] = None
    source_line: Optional[int] = None
    source_col: Optional[int] = None
    
    def get_operands(self) -> List[IRValue]:
        return []

    def has_side_effects(self) -> bool:
        return False

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
    
    def get_operands(self) -> List[IRValue]:
        return [self.left, self.right]

    def __repr__(self) -> str:
        return f"{self.result} = {self.op} {self.left.id} {self.right.id}"

@dataclass(kw_only=True)
class Call(IRInstruction):
    func_name: str
    args: List[IRValue]
    
    def get_operands(self) -> List[IRValue]:
        return self.args

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        res = f"{self.result} = " if self.result else ""
        return f"{res}call {self.func_name}({args_str})"

@dataclass(kw_only=True)
class UICall(IRInstruction):
    func_name: str
    args: List[IRValue] = field(default_factory=list)
    body: Optional[IRBlock] = None
    keywords: Dict[str, Union[IRValue, IRBlock]] = field(default_factory=dict)
    
    def get_operands(self) -> List[IRValue]:
        ops = self.args.copy()
        for v in self.keywords.values():
            if isinstance(v, IRValue):
                ops.append(v)
        return ops

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        kws_str = ", ".join(f"{k}={v}" for k, v in self.keywords.items())
        all_args = ", ".join(filter(None, [args_str, kws_str]))
        body_str = f" {{\n  {self.body}\n}}" if self.body else ""
        return f"ui_call {self.func_name}({all_args}){body_str}"

@dataclass(kw_only=True)
class StateInit(IRInstruction):
    initial_value: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.initial_value]

    def __repr__(self) -> str:
        return f"{self.result} = state_init({self.initial_value.id})"

@dataclass(kw_only=True)
class StateGet(IRInstruction):
    state_var: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.state_var]

    def __repr__(self) -> str:
        return f"{self.result} = state_get({self.state_var.id})"

@dataclass(kw_only=True)
class StateSet(IRInstruction):
    state_var: IRValue
    new_value: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.state_var, self.new_value]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"state_set({self.state_var.id}, {self.new_value.id})"

@dataclass(kw_only=True)
class ChannelInit(IRInstruction):
    def __repr__(self) -> str:
        return f"{self.result} = channel_init()"

@dataclass(kw_only=True)
class ChannelSend(IRInstruction):
    channel: IRValue
    value: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.channel, self.value]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"channel_send({self.channel.id}, {self.value.id})"

@dataclass(kw_only=True)
class ChannelCollect(IRInstruction):
    channel: IRValue
    body: IRBlock
    
    def get_operands(self) -> List[IRValue]:
        return [self.channel]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"channel_collect({self.channel.id}) {{\n  {self.body}\n}}"

@dataclass(kw_only=True)
class ServiceStart(IRInstruction):
    func_name: str
    
    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"service_start({self.func_name})"

@dataclass(kw_only=True)
class ServiceStop(IRInstruction):
    func_name: str
    
    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"service_stop({self.func_name})"

@dataclass(kw_only=True)
class NavigatorPush(IRInstruction):
    screen_func: str
    kwargs: Dict[str, IRValue]

    def get_operands(self) -> List[IRValue]:
        return list(self.kwargs.values())

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={v.id}" for k, v in self.kwargs.items())
        return f"navigator_push({self.screen_func}, {args})"

@dataclass(kw_only=True)
class NavigatorPop(IRInstruction):
    result: Optional[IRValue] = None

    def get_operands(self) -> List[IRValue]:
        return [self.result] if self.result else []

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"navigator_pop({self.result.id if self.result else ''})"

@dataclass(kw_only=True)
class Jump(IRInstruction):
    target_label: str
    
    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"jump {self.target_label}"

@dataclass(kw_only=True)
class Branch(IRInstruction):
    condition: IRValue
    true_label: str
    false_label: str
    
    def get_operands(self) -> List[IRValue]:
        return [self.condition]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"branch {self.condition.id}, {self.true_label}, {self.false_label}"

@dataclass(kw_only=True)
class ClassInit(IRInstruction):
    class_name: str
    args: List[IRValue]
    
    def get_operands(self) -> List[IRValue]:
        return self.args

    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        return f"{self.result} = new {self.class_name}({args_str})"

@dataclass(kw_only=True)
class TryExcept(IRInstruction):
    body: IRBlock
    handler: IRBlock
    exc_name: Optional[str] = None # 'e' in except Exception as e
    
    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"try {{\n{self.body}\n}} except {self.exc_name or ''} {{\n{self.handler}\n}}"

@dataclass(kw_only=True)
class IRIf(IRInstruction):
    condition: IRValue
    then_block: IRBlock
    else_block: Optional[IRBlock] = None
    
    def get_operands(self) -> List[IRValue]:
        return [self.condition]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"if {self.condition.id} {{\n{self.then_block}\n}} else {{\n{self.else_block}\n}}"

@dataclass(kw_only=True)
class Raise(IRInstruction):
    value: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.value]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"raise {self.value.id}"

@dataclass(kw_only=True)
class AttributeGet(IRInstruction):
    obj: IRValue
    attr_name: str
    
    def get_operands(self) -> List[IRValue]:
        return [self.obj]

    def __repr__(self) -> str:
        return f"{self.result} = {self.obj.id}.{self.attr_name}"

@dataclass(kw_only=True)
class AttributeSet(IRInstruction):
    obj: IRValue
    attr_name: str
    value: IRValue
    
    def get_operands(self) -> List[IRValue]:
        return [self.obj, self.value]

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{self.obj.id}.{self.attr_name} = {self.value.id}"

@dataclass(kw_only=True)
class MethodCall(IRInstruction):
    obj: IRValue
    method_name: str
    args: List[IRValue]
    
    def get_operands(self) -> List[IRValue]:
        return [self.obj] + self.args

    def has_side_effects(self) -> bool:
        return True

    def __repr__(self) -> str:
        args_str = ", ".join(v.id for v in self.args)
        res = f"{self.result} = " if self.result else ""
        return f"{res}method_call {self.obj.id}.{self.method_name}({args_str})"

@dataclass(kw_only=True)
class Return(IRInstruction):
    value: Optional[IRValue] = None
    
    def get_operands(self) -> List[IRValue]:
        return [self.value] if self.value else []

    def has_side_effects(self) -> bool:
        return True

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
    classes: List[IRClass] = field(default_factory=list)
    
    def __repr__(self) -> str:
        items = [repr(c) for c in self.classes] + [repr(f) for f in self.functions]
        return "\n\n".join(items)
