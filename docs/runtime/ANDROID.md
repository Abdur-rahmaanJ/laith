# Android Runtime

The Laith Android Runtime provides the necessary infrastructure for the compiled code to execute on an Android device.

## Core Components

- **PythonRuntime**: A singleton object that manages the global `CoroutineScope` and handles initialization/shutdown.
- **LaithWorker**: An abstract `CoroutineWorker` that serves as the base for all background tasks generated from Python. It handles error reporting and execution lifecycle.
- **LaithService**: An abstract `Service` for long-running foreground tasks. It manages its own `CoroutineScope` and handles automated `startForeground` with generated notifications.

## Build System Integration

The runtime is designed to work with an auto-generated Android project:
- **AndroidManifest.xml**: Automatically includes `<service>` and `<receiver>` entries.
- **CMake & NDK**: Uses a generated `CMakeLists.txt` to compile C++ performance layers into a shared library (`laith-native`) that is loaded by the Kotlin runtime.
