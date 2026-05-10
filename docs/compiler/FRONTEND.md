# Compiler Frontend

The frontend is responsible for translating Python source code into a verified symbol table and an AST ready for IR conversion.

## Semantic Analysis

The `SemanticAnalyzer` (in `laith/compiler/frontend/analyzer.py`) performs a single-pass traversal of the AST:

- **Type Resolution**: Maps Python type hints (`int`, `str`, etc.) to internal `Type` objects.
- **Scope Management**: Handles global, function, and block-level scopes using the `Scope` class.
- **Annotation Extraction**: Parses decorators to identify system behaviors.

### Supported Annotations

- `@periodic_task(interval="...", requires_wifi=bool, requires_charging=bool)`: Signals a background worker requirement with WorkManager constraints.
- `@foreground_service(notification="...")`: Defines an Android Foreground Service with automated notification management.
- `@native`: Marks a function for high-performance C++ compilation and automated JNI bridging.

### Built-in Functions & Classes

- **UI Components**: `Column`, `Row`, `Box`, `Text`, `Button` trigger Jetpack Compose IR nodes.
- **State Management**: `state(initial_value)` creates a reactive variable synchronized between background and UI.
- **IPC**: `Channel()` provides a `publish`/`collect` mechanism for event-based communication.
- **Service Control**: `start_service(func)` and `stop_service(func)` manage service lifecycles dynamically.
