# Laith

Python → Native Android Compiler Platform.

## Why

I have been doing React Native for half a year and i wanted to dive into Android and RN internals.
After diving i wondered why we don't have a similar project for Python.
I coded this by not following existing projects approaches. 

## What Laith means

Laith (ليث) means lion and is the name of my cat. Could not find a better name.

## Architecture

- **Frontend**: AST-based semantic analysis and type inference.
- **IR**: SSA-based Intermediate Representation.
- **Optimizer**: Multi-pass IR optimization (DCE, Constant Folding).
- **Backend**: Multi-layered emission (Kotlin/Compose + Native C++/JNI).
- **Orchestrator**: Automated Gradle/NDK build system and ADB device runner.

## Usage

```bash
# Initialize a professional project
laith init myapp

# Compile the default entry point (src/main.py)
laith build

# Build the native Android APK
laith compile

# The "Inner Loop": Build, Install, Run, and Stream Logs
laith run
```

## Project Configuration (`laith.toml`)

Laith uses a declarative, versioned manifest to manage the full Android lifecycle.

```toml
# laith.toml
version = "1.0"

[app]
name = "MyAwesomeApp"
namespace = "com.company.awesome"
identity = { id = "com.company.awesome", version_code = 42, version_name = "2.1.0" }

[sdk]
min = 26
target = 34
compile = 34

[dependencies]
implementation = [
    "com.squareup.retrofit2:retrofit:2.9.0",
    "androidx.compose.material3:material3:1.2.0"
]

[features]
compose = true
native = true
```

## Ai Contribution Policy

This project uses AI. If you use Ai and bring sensible improvement, then great. If it's mindless slop, then it wont get reviewed.

## Core Principles

1. **No embedded CPython**: No interpreter overhead; small binaries and fast startup.
2. **Compiled, not interpreted**: Statically analyzed and optimized for the Android runtime.
3. **Native Stack Alignment**: Direct mapping to Compose, Coroutines, and WorkManager.
4. **Zero-JNI Performance**: Automated C++ and JNI bridge generation for native code.

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
*   **Classes & Inheritance**: Custom class definitions are planned for Phase 6.
*   **Exception Handling**: `try`/`except` blocks are planned for Phase 7.

## Complete Application Demo

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

# 4. Native Android UI (Jetpack Compose)
def main_ui():
    # Collect updates from background channel
    msg_channel.collect(lambda data: print(data))

    Column(
        Text("Laith Native Platform"),
        Text(f"Global Counter: {counter.value}"),

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
*   **No Interpreter**: Kivy and BeeWare bundle a full CPython interpreter (libpython) inside your APK. Laith **statically compiles** Python into Kotlin/JVM and C++.
*   **Native UI**: Laith generates real **Jetpack Compose** code, using the exact same primitives as modern Android apps, rather than OpenGL custom views.

### vs. React Native
*   **No Runtime Bridge**: React Native relies on a JavaScript bridge. Laith eliminates this overhead by compiling everything to native bytecode or JNI-linked C++ before the app even runs.
*   **Type Safety**: Laith enforces a strictly typed subset, catching errors at compile-time that would be runtime crashes in JS.

### vs. Flutter
*   **Ecosystem Alignment**: Laith embraces the **Android Native Stack**, mapping Python directly to Kotlin Coroutines, WorkManager, and Jetpack Compose.
*   **Direct NDK Access**: While Flutter requires complex MethodChannels, Laith allows you to mark Python functions with `@native` to generate optimized C++ and automated JNI bridges instantly.
