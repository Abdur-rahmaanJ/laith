# Laith

Python → Native Android Compiler Platform.

## Architecture

- **Frontend**: AST-based semantic analysis and type inference.
- **IR**: SSA-based Intermediate Representation.
- **Backend**: Kotlin/JVM emitter with coroutine and Compose support.
- **Runtime**: Kotlin-native support for background tasks and async.

## Usage

```bash
# Initialize a project
laith init myapp

# Build a Python file to Kotlin
laith build src/main.py -o build/main.kt

# Compile the Android app
laith compile
```

## Core Principles

1. No embedded CPython.
2. Compiled, not interpreted.
3. Android-native abstractions (Compose, WorkManager).
4. Strictly typed subset of Python.

## Supported Python Subset

Laith currently supports a statically-analyzed subset of Python 3.10+:

*   **Syntax**: `def`, `async def`, `return`, assignments, and hierarchical function calls.
*   **Types**: `int`, `str`, `bool`, and `void` (explicit annotations or inferred).
*   **Async/Await**: Full mapping to Kotlin Coroutines for non-blocking I/O and UI.
*   **State Management**: `state(initial_value)` for reactive UI/background synchronization.
*   **IPC**: `Channel()` for event-based communication between layers.
*   **UI Components**: Jetpack Compose DSL (`Column`, `Row`, `Box`, `Text`, `Button`).
*   **Native**: `@native` decorator for high-performance C++ implementation.
*   **Background**: `@periodic_task` (WorkManager) and `@foreground_service` (Android Services).

## Not Supported (Yet)

To maintain high performance and static predictability, the following Python features are **not supported**:

*   **Dynamic Execution**: `eval()`, `exec()`, and dynamic `__import__()`.
*   **Runtime Metaprogramming**: Metaclasses, monkey patching, and dynamic attribute injection.
*   **Reflection**: Unrestricted `getattr`/`setattr` on arbitrary objects.
*   **Classes & Inheritance**: While planned for Phase 6, custom class definitions and complex inheritance are currently not supported.
*   **Exception Handling**: `try`/`except` blocks (planned for Phase 7).
*   **Standard Library**: Most of Python's standard library is not available unless explicitly mapped to Android equivalents.

## Complete Application Demo

Here is a comprehensive example demonstrating UI, reactive global state, background tasks, and native performance:

```python
# global_app.py
from laith import (
    state, Channel, native, periodic_task, 
    foreground_service, start_service, Column, Text, Button, Row
)

# 1. Reactive Global State
counter = state(0)
msg_channel = Channel()

# 2. Native C++ Layer (Zero-JNI)
@native
def compute_heavy_task(x: int) -> int:
    return x * x + 42

# 3. Background Task (WorkManager)
@periodic_task(interval="15m", requires_wifi=True)
async def sync_data():
    current = counter.value
    counter.set(current + 1)
    msg_channel.publish("Data synced from background")

# 4. Foreground Service
@foreground_service(notification="Location Tracking Active")
async def tracker():
    print("Service is running...")

# 5. Native Android UI (Jetpack Compose)
def main_ui():
    # Collect updates from background channel
    msg_channel.collect(lambda data: print(data))

    Column(
        Text("Laith Native Platform"),
        Text(f"Global Counter: {counter.value}"),

        Button("Start Service", on_click=lambda: start_service(tracker)),
        Button("Compute Native", on_click=lambda: print(compute_heavy_task(10))),

        Row(
            Button("Increment", on_click=lambda: counter.set(counter.value + 1)),
            Button("Reset", on_click=lambda: counter.set(0))
        )
    )
```

## Why Laith? (Comparison)

Laith represents a fundamental shift in how Python is used for mobile development. Unlike existing tools that wrap an interpreter, Laith treats Python as a high-level frontend for a native compiler.

### vs. Kivy & BeeWare
*   **No Interpreter**: Kivy and BeeWare bundle a full CPython interpreter (libpython) inside your APK, leading to large binaries and slower startup. Laith **statically compiles** Python into Kotlin/JVM and C++.
*   **Native UI**: Kivy uses a custom OpenGL-based rendering engine that doesn't "feel" native. BeeWare wraps native widgets but still runs on an interpreter. Laith generates real **Jetpack Compose** code, using the exact same primitives as modern Android apps.

### vs. React Native
*   **No Runtime Bridge**: React Native relies on a JavaScript bridge to communicate with native modules at runtime. Laith eliminates this overhead by compiling everything to native bytecode or JNI-linked C++ before the app even runs.
*   **Type Safety**: Laith enforces a strictly typed subset of Python, catching errors at compile-time that would be runtime crashes in a standard JS/Python environment.

### vs. Flutter
*   **Ecosystem Alignment**: Flutter uses a custom rendering engine (Skia/Impeller) that bypasses the Android View system. Laith embraces the **Android Native Stack**, mapping Python directly to Kotlin Coroutines, WorkManager, and Jetpack Compose.
*   **Direct NDK Access**: While Flutter requires complex MethodChannels for native logic, Laith allows you to mark Python functions with `@native` to generate optimized C++ and automated JNI bridges instantly.
