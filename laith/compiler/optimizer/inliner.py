from laith.compiler.ir.nodes import IRModule, IRFunction, IRBlock, IRInstruction, IRValue, Call, Return, Jump, BinaryOp, Constant, UICall, AttributeGet, AttributeSet, StateInit, StateGet, StateSet
from laith.compiler.optimizer.base import OptimizerPass
from typing import Dict, Optional, List, Any
import copy

class InlinerPass(OptimizerPass):
    """
    Inlines small functions to reduce call overhead.
    """
    def __init__(self, threshold: int = 15):
        self.threshold = threshold
        self.value_counter = 1000 # High range for inlined values

    def run(self, module: IRModule):
        # 1. Identify candidates (leaf functions, no recursion, small)
        inline_candidates: Dict[str, IRFunction] = {}
        for func in module.functions:
            if func.name == "global_init" or func.name == "main_ui":
                continue
            # Don't inline UI, services, or native
            is_special = any(d["name"] in ["periodic_task", "foreground_service", "native", "Composable"] for d in func.decorators)
            if not is_special and len(func.blocks) == 1 and len(func.blocks[0].instructions) < self.threshold:
                 inline_candidates[func.name] = func

        if not inline_candidates:
            return

        # 2. Perform inlining (one pass)
        for func in module.functions:
            for block in func.blocks:
                new_instructions = []
                for inst in block.instructions:
                    if isinstance(inst, Call) and inst.func_name in inline_candidates:
                        target = inline_candidates[inst.func_name]
                        new_instructions.extend(self._inline(target, inst))
                    else:
                        new_instructions.append(inst)
                block.instructions = new_instructions

    def _inline(self, target: IRFunction, call_inst: Call) -> List[IRInstruction]:
        # 1. Map parameters to call arguments
        # mapping: target_param_id -> caller_arg_val
        val_map: Dict[str, IRValue] = {}
        for i, param in enumerate(target.args):
            val_map[param.id] = call_inst.args[i]

        inlined_insts = []
        target_block = target.blocks[0]
        
        # 2. Remap internal values
        for inst in target_block.instructions:
            if isinstance(inst, Return):
                if inst.value and call_inst.result:
                    # In SSA, we'd need a Phi or Rename. 
                    # For now, we'll emit a direct 'copy' (BinaryOp add 0) 
                    # or just a mapping if we were doing a recursive remapper.
                    # Let's emit a BinaryOp 'add' with 0 as a move.
                    res_val = self._remap_val(inst.value, val_map)
                    # Use the CALL's result as the target of this 'move'
                    # Actually, we can't easily do that without breaking SSA in the caller
                    # unless we are careful.
                    # Simpler: just replace all uses of call_inst.result with res_val?
                    # But we are in an optimizer, not re-builder.
                    # Best: emit a Constant + BinaryOp move.
                    zero = IRValue(id=f"inline_zero_{self.value_counter}", type=res_val.type)
                    self.value_counter += 1
                    inlined_insts.append(Constant(result=zero, value=0))
                    inlined_insts.append(BinaryOp(result=call_inst.result, op="add", left=res_val, right=zero))
                continue
            
            # Clone and remap operands/result
            new_inst = copy.copy(inst)
            if inst.result:
                 new_res = IRValue(id=f"i_{inst.result.id}_{self.value_counter}", type=inst.result.type)
                 val_map[inst.result.id] = new_res
                 new_inst.result = new_res
                 self.value_counter += 1
            
            # Remap operands
            if isinstance(new_inst, BinaryOp):
                 new_inst.left = self._remap_val(new_inst.left, val_map)
                 new_inst.right = self._remap_val(new_inst.right, val_map)
            elif isinstance(new_inst, Call):
                 new_inst.args = [self._remap_val(a, val_map) for a in new_inst.args]
            elif isinstance(new_inst, AttributeGet):
                 new_inst.obj = self._remap_val(new_inst.obj, val_map)
            elif isinstance(new_inst, AttributeSet):
                 new_inst.obj = self._remap_val(new_inst.obj, val_map)
                 new_inst.value = self._remap_val(new_inst.value, val_map)
            elif isinstance(new_inst, StateSet):
                 new_inst.state_var = self._remap_val(new_inst.state_var, val_map)
                 new_inst.new_value = self._remap_val(new_inst.new_value, val_map)
            elif isinstance(new_inst, StateGet):
                 new_inst.state_var = self._remap_val(new_inst.state_var, val_map)

            inlined_insts.append(new_inst)
            
        return inlined_insts

    def _remap_val(self, val: IRValue, val_map: Dict[str, IRValue]) -> IRValue:
        return val_map.get(val.id, val)
