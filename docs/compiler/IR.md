# SSA Intermediate Representation (IR)

Laith uses a custom SSA-based IR to bridge the gap between Python's high-level AST and low-level target code.

## IR Nodes

Located in `laith/compiler/ir/nodes.py`:

- **IRFunction**: Represents a compiled function, including its return type, parameters, and basic blocks.
- **IRBlock**: A linear sequence of instructions ending in a terminator.
- **IRValue**: Represents an SSA variable with a specific ID and Type.
- **IRInstruction**: 
    - `Constant`: Literals (int, str, bool).
    - `BinaryOp`: Standard arithmetic and logical operations.
    - `Call`: Standard function calls.
    - `UICall`: Specialized node for Jetpack Compose, supporting a nested `IRBlock` for trailing lambdas.
    - `StateInit/Get/Set`: Instructions for managing reactive `state()`.
    - `ChannelInit/Send/Collect`: IPC primitives for `Channel()` communication.
    - `ServiceStart/Stop`: Control nodes for starting and stopping background services.

## IR Construction

The `IRBuilder` (in `laith/compiler/ir/builder.py`) transforms the AST. It uses the `Scope` information from the Frontend to ensure correct type propagation and symbol resolution.
