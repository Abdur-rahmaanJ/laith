from laith.compiler.optimizer.base import Pass
from laith.compiler.ir.nodes import IRModule, IRFunction, IRBlock, IRInstruction, IRValue, Constant, BinaryOp

class ConstantFoldingPass(Pass):
    def run(self, module: IRModule) -> bool:
        changed = False
        for func in module.functions:
            if self._run_on_func(func):
                changed = True
        return changed

    def _run_on_func(self, func: IRFunction) -> bool:
        changed = False
        
        # Map of IRValue ID to its constant value
        const_map = {}

        def fold_block(block: IRBlock) -> bool:
            nonlocal changed
            block_changed = False
            
            new_insts = []
            for inst in block.instructions:
                if isinstance(inst, Constant):
                    const_map[inst.result.id] = inst.value
                    new_insts.append(inst)
                    continue
                
                if isinstance(inst, BinaryOp):
                    if inst.left.id in const_map and inst.right.id in const_map:
                        lval = const_map[inst.left.id]
                        rval = const_map[inst.right.id]
                        
                        try:
                            if inst.op == "add": res = lval + rval
                            elif inst.op == "sub": res = lval - rval
                            elif inst.op == "mul": res = lval * rval
                            elif inst.op == "div": res = lval / rval
                            else: res = None
                            
                            if res is not None:
                                # Replace BinaryOp with Constant
                                new_inst = Constant(result=inst.result, value=res)
                                const_map[inst.result.id] = res
                                new_insts.append(new_inst)
                                block_changed = True
                                changed = True
                                continue
                        except Exception:
                            pass # Fallback to original inst

                # For other instructions, just check nested blocks
                if hasattr(inst, 'body') and inst.body:
                    if fold_block(inst.body):
                        block_changed = True
                if hasattr(inst, 'keywords'):
                    for v in inst.keywords.values():
                        if isinstance(v, IRBlock):
                            if fold_block(v):
                                block_changed = True
                
                new_insts.append(inst)
            
            block.instructions = new_insts
            return block_changed

        for block in func.blocks:
            if fold_block(block):
                changed = True
        
        return changed
