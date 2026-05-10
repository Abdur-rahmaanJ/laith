# Kotlin Backend

The Kotlin backend is the primary target for Phase 1. It generates human-readable, high-performance Kotlin code.

## Type Mapping

Python types are mapped to Kotlin types in `laith/compiler/backend/kotlin/mapping.py`:
- `int` -> `Int`
- `str` -> `String`
- `bool` -> `Boolean`
- `void` -> `Unit`

## Code Emission

The `KotlinEmitter` (in `laith/compiler/backend/kotlin/emitter.py`) handles the translation:

- **Functions**: Python functions become Kotlin `fun`. Async functions become `suspend fun`.
- **Background Tasks**: Decorators like `@periodic_task` trigger the generation of a `CoroutineWorker` class that wraps the target function.
- **UI Components**: `UICall` nodes are emitted as Compose functions. If a `UICall` has a body, it is emitted using Kotlin's trailing lambda syntax: `Column { ... }`.
- **Global State**: Global variables use `MutableStateFlow`. When accessed in a `@Composable`, the emitter generates `collectAsState().value` to ensure reactivity.
- **Native Integration**: 
    - Functions marked `@native` generate `external` declarations in a `NativeLib` companion object.
    - Native routing ensures calls to these functions are directed through the JNI-linked library.
- **Task Scheduling**: A `scheduleLaithTasks` function is generated to register all WorkManager tasks on app startup.
