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

- Downloading Android studio normally downloads required tools
- Make sure Adb is installed

```bash
# pip install laith
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
*   **Object-Oriented Logic**: Support for `class` definitions, `__init__` constructors, and instance methods with `self` attribute access.
*   **Automated SDK Bridge**: Direct access to **any** Android API (e.g., `android.os.Build`, `android.os.Vibrator`) via real-time bytecode analysis.
*   **Smart Permissions**: Automatic `AndroidManifest.xml` generation; the compiler infers required permissions based on your Python code.
*   **Async/Await**: Full mapping to Kotlin Coroutines for non-blocking I/O and UI.
*   **Diagnostics**: Source Maps for Python-aware stack traces; Android errors are mapped back to original Python line numbers.
*   **State Management**: `state(initial_value)` for reactive UI/background synchronization.
*   **UI Components**: Jetpack Compose DSL (`Column`, `Row`, `Box`, `Text`, `Button`).
*   **Optimized Native Performance**: `@native` C++ compilation and automatic function inlining.
*   **Background Tasks**: `@periodic_task` (WorkManager) and `@foreground_service` (Android Services).

## Not Supported (Yet)

To maintain high performance and static predictability, the following Python features are **not supported**:

*   **Dynamic Execution**: `eval()`, `exec()`, and dynamic `__import__()`.
*   **Runtime Metaprogramming**: Metaclasses, monkey patching, and dynamic attribute injection.
*   **Reflection**: Unrestricted `getattr`/`setattr` on arbitrary objects.
*   **Exception Handling**: `try`/`except` blocks are planned for Phase 12.

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

## Dynamic bridge

```python
from laith import Column, Text, Button

def open_docs():
    url = "https://compilercalchemy.com"
    # Intent and Uri are auto-resolved to android.content.Intent and android.net.Uri
    # see docs/api.md
    # no import needed
    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    context.startActivity(intent)

def main_ui():
    Column(
        Text("Laith Intent Lab"),
        Text("Click the button below to open the official documentation."),
        Button("Visit Documentation", on_click=lambda: open_docs())
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

## Why build with Laith?

### Write Python, Ship Native

You write Python — Laith compiles it to **real** Jetpack Compose, Kotlin coroutines, and C++ via the NDK. No interpreter bundled. No bridge latency. Your app starts fast and stays fast.

```python
def main_ui():
    count = state(0)
    Scaffold(
        top_bar=TopAppBar(),
        body=Column(
            Text(f"Taps: {count}"),
            Button("Tap me", on_click=lambda: count.set(count.value + 1)),
        ),
    )
```

### Everything you need to ship

| You get this | So you can... |
|---|---|
| **40+ Material3 widgets** | Build any UI — inputs, dialogs, snackbars, lazy lists, navigation bars, bottom sheets |
| **LazyColumn / LazyRow** | Render large lists efficiently with automatic recycling |
| **Stack Navigator** | Push/pop screens with params, deep linking via `@route` |
| **Theme + dark mode** | One `Theme()` call generates Material3 light + dark color schemes + Android 12+ dynamic colors |
| **Reactive state** | `state()` with automatic UI sync — no boilerplate observers |
| **SQLite + Preferences + FileStorage + SecureStorage** | Persist data: relational, key-value, encrypted, or raw files |
| **Async HTTP client** | `await http.get(url)` with JSON parsing |
| **`resource()` pattern** | Loading/error/retry state management for async data |
| **`on_mount` / `on_dispose` / `on_resume` / `on_pause` / `effect()`** | Lifecycle hooks for sensors, timers, data loading, reactive side effects |
| **`@periodic_task` + `@foreground_service`** | Background work via WorkManager and Android Services |
| **`@requires_permission` + `remember_permission`** | Declarative runtime permission handling |
| **`AndroidView`** | Embed any native Android view (Maps, WebView, ExoPlayer, CameraX) |
| **`@native` C++** | Mark hot functions for NDK compilation — zero JNI overhead |
| **`laith doctor`** | Verify your JDK, Android SDK, and ADB setup in one command |
| **Source maps** | Android crashes show Python line numbers, not Kotlin |
| **`laith watch`** | Live-reload on device when you save a file |
| **ProGuard / R8 + signing** | Release builds with obfuscation, keystore config with env var fallback |

### No magic, no lock-in

The generated output is **readable Kotlin** with your original Python names preserved (snake_case → camelCase, with source comments). You can open it in Android Studio and debug like any native project. If Laith ever stops being the right fit, you keep the code.
