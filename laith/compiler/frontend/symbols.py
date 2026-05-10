from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, List, Any

class SymbolKind(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    CLASS = auto()
    PARAMETER = auto()

@dataclass(frozen=True)
class Type:
    name: str
    
    def __repr__(self) -> str:
        return self.name

# Built-in types
VOID_TYPE = Type("void")
INT_TYPE = Type("int")
STR_TYPE = Type("str")
BOOL_TYPE = Type("bool")
ANY_TYPE = Type("any")

@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    type: Type = ANY_TYPE
    is_async: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class Scope:
    def __init__(self, parent: Optional[Scope] = None, name: str = "global", kind: str = "module"):
        self.parent = parent
        self.name = name
        self.kind = kind
        self.symbols: Dict[str, Symbol] = {}
        self.children: List[Scope] = []

    def define(self, symbol: Symbol) -> None:
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def create_child(self, name: str, kind: str = "function") -> Scope:
        child = Scope(parent=self, name=name, kind=kind)
        self.children.append(child)
        return child

    def __repr__(self) -> str:
        return f"Scope({self.name}, symbols={list(self.symbols.keys())})"
