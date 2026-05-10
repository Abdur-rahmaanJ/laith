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

# You can just do:
# $ laith init myapp
# $ cd my app
# $ laith run
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
from laith import Column, Text, Button, vibrate

def main_ui():
    Column(
        Text("Laith Vibe Lab"),
        Text("Press buttons to test haptic feedback"),
        
        Button("Quick Vibe (100ms)", on_click=lambda: vibrate(100)),
        Button("Medium Vibe (500ms)", on_click=lambda: vibrate(500)),
        Button("Long Vibe (1s)", on_click=lambda: vibrate(1000))
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

## Laith Feature Matrix

| Category | Feature | Phase | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Syntax** | Basic Constructs | 1 | ✅ Done | Support for `def`, `async def`, `return`, `if`, and assignments. |
| **Syntax** | Type Inference | 1 | ✅ Done | Static analysis of `int`, `str`, `bool`, and `void` types. |
| **Syntax** | Async/Await | 3 | ✅ Done | Direct mapping of Python `async` to Kotlin Coroutines. |
| **Syntax** | For-Loops | 6 | ✅ Done | Basic `for i in range(n)` support in IR and backends. |
| **OO Model** | Custom Classes | 6 | ✅ Done | Support for `class` definitions and instance attributes. |
| **OO Model** | Constructors | 6 | ✅ Done | Support for `__init__` mapping to Kotlin initialization logic. |
| **OO Model** | Instance Methods | 6 | ✅ Done | Methods with `self` binding and attribute access. |
| **State** | Reactive State | 2 | ✅ Done | `state(value)` for UI-synchronized global or instance variables. |
| **State** | State Observation | 6 | ✅ Done | Automatic `collectAsState()` for class-member reactive state. |
| **IPC** | Channels | 4 | ✅ Done | `Channel()` for asynchronous event-driven communication. |
| **UI** | Compose DSL | 2 | ✅ Done | High-fidelity mapping to `Column`, `Row`, `Box`, `Text`, `Button`. |
| **UI** | Theming | 7 | ✅ Done | Automated generation of Material3 themes and adaptive icons. |
| **Hardware** | SDK Bridging | 7 | ✅ Done | Dynamic access to any Android API (e.g., `Build.MODEL`). |
| **Hardware** | API Discovery | 7 | ✅ Done | Real-time bytecode analysis of `android.jar` for symbol lookup. |
| **Hardware** | Smart Permissions | 7 | ✅ Done | Automatic `uses-permission` injection via code inference. |
| **Native** | @native C++ | 5 | ✅ Done | Direct compilation of Python functions to optimized C++ via NDK. |
| **Native** | Zero-JNI | 5 | ✅ Done | Automated JNI bridge and name mangling generation. |
| **Background** | Periodic Tasks | 3 | ✅ Done | `@periodic_task` mapping to Android WorkManager. |
| **Background** | Services | 3 | ✅ Done | `@foreground_service` for long-running Android components. |
| **Optimizers** | Constant Folding | 4 | ✅ Done | Compile-time evaluation of constant expressions. |
| **Optimizers** | Dead Code (DCE) | 4 | ✅ Done | Automatic removal of unused instructions and variables. |
| **Tooling** | CLI Orchestrator | 1 | ✅ Done | Unified `init`, `build`, `compile`, and `run` commands. |
| **Tooling** | "Inner Loop" | 7 | ✅ Done | ABI-targeted `installDebug` with real-time logcat streaming. |
| **Syntax** | Exceptions | 8 | 🛠️ Planned | `try` / `except` blocks for native error handling. |
| **Optimizers** | Advanced Opts | 9 | 🛠️ Planned | Inlining, escape analysis, and loop unrolling. |
| **Tooling** | LSP / IDE | 10 | 🛠️ Planned | VSCode extension for type hints and autocomplete. |
