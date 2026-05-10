# SSA Intermediate Representation (IR)

Laith uses a custom SSA-based IR to bridge the gap between Python's high-level AST and low-level target code.

## Core Concepts

- **Static Single Assignment (SSA)**: Every value is assigned exactly once. This simplifies data-flow analysis for the optimizer.
- **Diagnostics**: Every `IRInstruction` carries `source_line` and `source_col` metadata linking it back to the original Python source.

## IR Nodes

Located in `laith/compiler/ir/nodes.py`:

### High-Level Structures
- **IRModule**: The top-level container for functions and classes.
- **IRClass**: Native representation of a Python class, containing `IRField` and `IRMethod` definitions.
- **IRFunction**: A global function or background task.

### Blocks & Values
- **IRBlock**: A linear sequence of instructions ending in a terminator (`Jump`, `Branch`, `Return`).
- **IRValue**: Represents an SSA variable with a unique ID and a `Type`.

### Instruction Set
- **Object Model**: `ClassInit`, `AttributeGet`, `AttributeSet`, `MethodCall`.
- **UI Logic**: `UICall` (Specialized for Jetpack Compose hierarchies).
- **Reactive State**: `StateInit`, `StateGet`, `StateSet`.
- **Arithmetic**: `BinaryOp` (add, sub, mul, div, etc.).
- **Constants**: `Constant` (int, str, bool).
- **IPC**: `ChannelInit`, `ChannelSend`, `ChannelCollect`.
- **Lifecycles**: `ServiceStart`, `ServiceStop`.

## IR Construction

The `IRBuilder` (in `laith/compiler/ir/builder.py`) recursively visits the AST, using the `SemanticAnalyzer`'s scope and type information to generate valid SSA form.
