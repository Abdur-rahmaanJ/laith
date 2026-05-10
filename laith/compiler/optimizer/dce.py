from laith.compiler.optimizer.base import Pass
from laith.compiler.ir.nodes import IRModule, IRFunction, IRBlock, IRInstruction, IRValue

class DCEPass(Pass):
    def run(self, module: IRModule) -> bool:
        # Collect all uses across the entire module
        uses = set()
        
        def collect_uses(block: IRBlock):
            for inst in block.instructions:
                for op in inst.get_operands():
                    uses.add(op.id)
                # Recursively check nested blocks
                if hasattr(inst, 'body') and inst.body:
                    collect_uses(inst.body)
                if hasattr(inst, 'keywords'):
                    for v in inst.keywords.values():
                        if isinstance(v, IRBlock):
                            collect_uses(v)

        for func in module.functions:
            for block in func.blocks:
                collect_uses(block)

        changed = False
        for func in module.functions:
            if self._run_on_func(func, uses):
                changed = True
        return changed

    def _run_on_func(self, func: IRFunction, uses: set) -> bool:
        changed = False
        
        def remove_dead(block: IRBlock) -> bool:
            nonlocal changed
            new_insts = []
            block_changed = False
            for inst in block.instructions:
                # If it has side effects, it's alive
                if inst.has_side_effects():
                    new_insts.append(inst)
                    # Still need to process nested blocks
                    if hasattr(inst, 'body') and inst.body:
                        if remove_dead(inst.body):
                            block_changed = True
                    if hasattr(inst, 'keywords'):
                        for v in inst.keywords.values():
                            if isinstance(v, IRBlock):
                                if remove_dead(v):
                                    block_changed = True
                    continue
                
                # If it has a result and the result is used anywhere in the module, it's alive
                if inst.result and inst.result.id in uses:
                    new_insts.append(inst)
                    continue
                
                print(f"DEBUG: Removing dead instruction: {inst}")
                block_changed = True
                changed = True
            
            block.instructions = new_insts
            return block_changed

        for block in func.blocks:
            if remove_dead(block):
                changed = True
        
        return changed
