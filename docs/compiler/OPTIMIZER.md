# IR Optimizer

The Laith optimizer (in `laith/compiler/optimizer`) performs static analysis and transformation of the Intermediate Representation to improve performance and reduce binary size.

## Pass-Based Architecture

The optimizer uses an iterative, multi-pass architecture:
1.  **Analysis**: Passes scan the IR to identify optimization opportunities.
2.  **Transformation**: Passes modify the IR nodes (e.g., remapping values, deleting instructions).
3.  **Fixed-Point**: Passes run iteratively until no further instructions can be optimized.

## Implemented Passes

### 1. Inlining (`InlinerPass`)
Reduces invocation overhead by replacing small function calls with their direct instruction sequence.
- **Heuristic**: Targets leaf functions under a specific instruction threshold.
- **Remapping**: Automatically remaps local SSA values to unique IDs to prevent collisions in the caller block.

### 2. Dead Code Elimination (`DCEPass`)
Aggressively removes instructions whose results are never used and which have no observable side effects.
- **Safety**: Always preserves `UICall`, `ServiceStart`, and `ChannelSend` nodes.

### 3. Constant Folding (`ConstantFoldingPass`)
Evaluates deterministic expressions at compile-time.
- **Scope**: Supports binary arithmetic on `int`, `str`, and `bool` literals.
- **Impact**: Enables deeper DCE by turning complex expressions into single constants.

## Advanced Strategies (Future)
- **Escape Analysis**: Promoting heap allocations to the stack for short-lived objects.
- **Loop Unrolling**: Expanding small constant-range loops to eliminate branch penalties.
