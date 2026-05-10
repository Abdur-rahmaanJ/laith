# IR Optimizer

The Laith optimizer (in `laith/compiler/optimizer`) performs static analysis and transformation of the Intermediate Representation to improve performance and reduce binary size.

## Architecture

The optimizer uses a pass-based architecture managed by the `Optimizer` class:

- **Pass Framework**: The base `Pass` class defines a standard interface for IR transformations.
- **Iterative Execution**: Optimization passes run iteratively until no further changes are detected (fixed-point iteration).

## Implemented Passes

### Dead Code Elimination (DCE)

The `DCEPass` identifies and removes instructions that are "dead":
- An instruction is dead if it has no side effects and its result is never used within the entire module.
- It preserves instructions with side effects like `UICall`, `Call`, `ServiceStart`, and `ChannelSend`.

### Constant Folding

The `ConstantFoldingPass` evaluates arithmetic expressions at compile-time:
- Identifies `BinaryOp` nodes where both operands are constants.
- Replaces the operation with a single `Constant` node.
- This reduces runtime computation and enables further DCE by eliminating temporary variables.

## Future Optimizations

- **Function Inlining**: Reducing call overhead for small functions.
- **Escape Analysis**: Identifying variables that don't leave a specific scope to optimize memory allocation.
- **Async Lowering**: Optimizing coroutine state machines for even lower latency.
