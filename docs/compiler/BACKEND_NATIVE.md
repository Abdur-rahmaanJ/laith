# Native Backend & JNI

Laith supports high-performance native execution via a dedicated C++ emission layer. This fulfills the "Selective Native Compilation" requirement for performance-sensitive tasks.

## C++ Emitter

The `CPPEmitter` (in `laith/compiler/backend/native/emitter.py`) extracts functions marked with the `@native` decorator:

- **Extern "C"**: Functions are emitted as C-compatible symbols to ensure they can be linked by JNI.
- **Optimized Types**: Maps Python/IR types to optimized C++ types (`int64_t`, `const char*`).
- **Direct Logic**: Translates IR instructions into equivalent C++ expressions.

## JNI Bridge Generation

The `JNIEmitter` (in `laith/compiler/backend/native/jni_emitter.py`) automates the boilerplate required for Android integration:

- **Function Name Mapping**: Generates JNI-compliant function names based on the project's Java package name.
- **Type Conversion**: Handles the mapping between JNI types (`jlong`, `jstring`) and the standard C++ implementation.
- **Zero-JNI Experience**: Developers never write JNI code manually; the compiler handles all ownership and bridge logic.

## NDK Integration

The CLI integrates these components into the Android build pipeline:

- **CMakeLists.txt**: Automatically generated to link the implementation and bridge files.
- **Gradle Linkage**: The `app/build.gradle.kts` file is configured to trigger the NDK build during the standard application compilation process.
- **Shared Library**: All native code is compiled into `liblaith-native.so`.
