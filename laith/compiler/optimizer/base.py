from abc import ABC, abstractmethod
from laith.compiler.ir.nodes import IRModule, IRFunction, IRBlock, IRInstruction

class Pass(ABC):
    @abstractmethod
    def run(self, module: IRModule) -> bool:
        """Run the pass on the module. Returns True if any changes were made."""
        pass

class Optimizer:
    def __init__(self):
        self.passes: list[Pass] = []

    def add_pass(self, p: Pass):
        self.passes.append(p)

    def optimize(self, module: IRModule):
        changed = True
        while changed:
            changed = False
            for p in self.passes:
                if p.run(module):
                    changed = True
