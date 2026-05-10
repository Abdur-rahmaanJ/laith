# Laith Architecture Overview

Laith is a statically compiled Python platform for Android. It transforms a typed subset of Python into high-performance native Android components without an embedded CPython interpreter.

## The Compilation Pipeline

1.  **Frontend (`laith/compiler/frontend`)**: 
    *   **Semantic Analysis**: Resolves symbols and types across module and class scopes.
    *   **Dynamic SDK Bridge**: Performs real-time bytecode analysis of `android.jar` to enable access to any Android API (e.g., `android.os.Build`).
    *   **Permission Inference**: Automatically detects required Android permissions based on API usage.

2.  **Intermediate Representation (`laith/compiler/ir`)**:
    *   **SSA Architecture**: Uses a Static Single Assignment IR for reliable optimization.
    *   **Object Model**: Native support for `IRClass`, `IRMethod`, and `IRField`.
    *   **Source Mapping**: IR nodes preserve Python source line/column metadata for diagnostics.

3.  **Optimizer (`laith/compiler/optimizer`)**:
    *   **DCE & Constant Folding**: Aggressive removal of unused code and compile-time evaluation.
    *   **Inlining**: Automatically replaces small function calls with direct instructions to reduce invocation overhead.

4.  **Backend (`laith/compiler/backend`)**:
    *   **Kotlin Emitter**: Generates coroutine-native, thread-safe Kotlin code with Jetpack Compose support.
    *   **Native Emitter**: Compiles functions marked with `@native` directly to optimized C++ via the NDK.
    *   **JNI Bridge**: Standardizes `extern "C"` linkage for zero-overhead communication between layers.

## Runtime & Tooling

### The "Inner Loop" Developer Experience
*   **`laith run`**: Orchestrates ABI-specific incremental builds, installation via ADB, and log streaming.
*   **Source Rewriting**: Automatically maps Android stack traces back to Python line numbers in real-time.
*   **`laith watch`**: High-performance file watcher for instant "Live Preview" on physical hardware.

### Production Readiness
*   **AAB Support**: Generates Google Play-compatible Android App Bundles.
*   **Automated Signing**: Orchestrates RSA keystore generation and secure property synchronization for release binaries.
