# Laith Architecture Overview

Laith is a statically compiled Python platform for Android. It transforms a typed subset of Python into native Android components without an embedded CPython interpreter.

## The Compilation Pipeline

1.  **Frontend (`laith/compiler/frontend`)**: 
    *   Parses Python source using the native `ast` module.
    *   Performs semantic analysis to resolve symbols and types.
    *   Identifies architectural annotations (decorators) like `@periodic_task` and `@native`.

2.  **Intermediate Representation (`laith/compiler/ir`)**:
    *   Converts the AST into a custom SSA-based (Static Single Assignment) IR.
    *   Supports reactive primitives (`state`, `Channel`) and service lifecycles.
    *   Maintains type information across all operations.

3.  **Optimizer (`laith/compiler/optimizer`)**:
    *   Performs multi-pass optimizations on the IR.
    *   Includes Dead Code Elimination (DCE) and Constant Folding.
    *   Ensures the generated code is lean and efficient.

4.  **Backend (`laith/compiler/backend`)**:
    *   **Kotlin Emitter**: Translates IR into thread-safe, coroutine-native Kotlin code with Jetpack Compose support.
    *   **Native Emitter**: Generates optimized C++ code for functions marked with `@native`.
    *   **JNI Bridge**: Automatically generates the C++ boilerplate for Kotlin-to-Native communication.

## Runtime System (`laith/runtime`)

The runtime is a thin Kotlin layer that provides:
*   **Coroutine Scope**: Managed lifecycle for Python tasks.
*   **Task Abstractions**: Base classes for `LaithWorker` and `LaithService`.
*   **Global State**: Bridge for `MutableStateFlow` to Compose `collectAsState()`.
*   **Compose Integration**: Bridges Python UI definitions to the Jetpack Compose runtime.

## Tooling (`laith/cli`)

The `laith` CLI provides the developer interface:
*   `init`: Scaffolds new projects with Gradle and NDK support.
*   `build`: Compiles Python source to optimized Kotlin, C++, and JNI.
*   `compile`: Orchestrates the Android build process (Gradle + CMake).
