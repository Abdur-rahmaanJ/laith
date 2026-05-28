# Changelog

All notable changes to Laith are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Crash overlay (RedBox-style)** — catches uncaught exceptions during UI composition and shows a full-screen error overlay with stack trace and "Reload App" button. Uses a Compose error boundary that wraps `mainUi()` in `CrashOverlay { ... }`. Runtime file auto-copies to generated projects. (`feat/crash-overlay`)
- **`KotlinComposable` interop** — call any Jetpack Compose function by fully-qualified name: `KotlinComposable("com.example.MyScreen", title="Hello")`. Registered as built-in, IR builder extracts the composable name from the first positional arg, emitter generates direct Kotlin calls. (`feat/kotlin-composable`)
- **Product flavors** — `[flavors.dev]`, `[flavors.prod]` sections in `laith.toml` with configurable `application_id`, `app_name`, `version_code`, `version_name`, `api_endpoint`. `--flavor` CLI option on `compile`, `run`, and `build` commands. Gradle template generates `flavorDimensions` and `productFlavors` block. Active flavor overrides merge into template context. (`feat/product-flavors`)
- **File download/upload with progress** — `http.download(url, localPath, on_progress=...)` and `http.upload(url, localPath, on_progress=...)` suspend functions with progress callbacks via function references. Emits `httpDownload`/`httpUpload` suspend helper functions. (`feat/download-upload`)
- **HTTP request/response interceptors** — `http.add_request_interceptor(func)` and `http.add_response_interceptor(func)` register interceptors that apply to every HTTP call. Request interceptors modify headers, response interceptors transform responses. (`feat/interceptors`)
- **Deep linking support** — `@route(path, scheme, host)` generates `NavHost` deep links and `<intent-filter>` entries in `AndroidManifest.xml`. `singleTask` launch mode with `onNewIntent` handling. (`feat/deep-linking`)

### Fixed

- **IR builder keyword arg handling** — fixed pre-existing bug where `fun_ref_` IRValues were not properly handled in both positional args and keyword args of method calls, affecting interceptors and download/upload.

## [0.2.0] - 2026-05-01

### Added

- **ProGuard/R8 release builds** — `laith build --release` generates obfuscation configs automatically. `laith bundle` for AAB output. Signing configuration in `laith.toml` with environment variable fallback (`LAITH_KEYSTORE_PATH`, etc.). Gradle template includes `release` build type with `isMinifyEnabled`.
- **AndroidView composable** — embed arbitrary Android views via `AndroidView(factory=lambda ctx: ...)`. Enables use of Maps, ExoPlayer, WebView, and any third-party Android view library.
- **Runtime permission handling** — `@requires_permission("CAMERA")` decorator generates manifest entries and runtime `checkSelfPermission` calls. `remember_permission(permission)` composable returns reactive permission state with `.granted`, `.should_show_rationale`, `.request()`.
- **Theme provider** — `Theme(primary=..., dark_primary=..., use_dynamic_colors=True)` generates `MaterialTheme` with `lightColorScheme`/`darkColorScheme`. Dynamic color support for Android 12+.
- **Lifecycle hooks** — `on_resume`/`on_pause` composable lifecycle hooks using `LifecycleEventObserver`.

### Changed

- Permission decorator parser updated to handle positional string arguments.
- All compiler tests (108+) passing.

## [0.1.0] - 2026-04-15

### Added

- **Initial compiler pipeline** — Python to Kotlin compilation with parser, semantic analyzer, IR builder, optimizer, and Kotlin emitter.
- **Core UI composables** — `Column`, `Row`, `Box`, `Text`, `Button`, `TextField`, `Checkbox`, `Switch`, `Slider`, `Image`, `Icon`, `Spacer`.
- **Material components** — `Scaffold` with `TopAppBar`, `BottomAppBar`, `FloatingActionButton`. `Dialog`, `AlertDialog`, `Snackbar`, `ModalBottomSheet`.
- **Lazy lists** — `LazyColumn`/`LazyRow` for efficient list rendering with automatic recycling.
- **Stack Navigator** — `Navigator.push(screen, params)` with parameter passing and `Navigator.pop(result)` for returning data. `@route` decorator for screen routing.
- **Back button handling** — system back → pop screen.
- **State management** — `state()` with reactive updates via `mutableStateOf`.
- **Preferences API** — `Preferences("app")` backed by `SharedPreferences` with `get`/`set`/`remove`/`contains` methods.
- **SQLite Database** — `Database("my.db")` with Pythonic `query()`/`execute()` methods backed by `android.database.sqlite`.
- **File Storage** — `FileStorage` with `read_text`/`write_text`/`read_bytes`/`write_bytes`/`delete`/`exists`/`get_cache_dir`/`get_files_dir`.
- **Secure Storage** — `SecureStorage` wrapping `EncryptedSharedPreferences` for encrypted key-value storage.
- **Async HTTP client** — `http.get(url, headers=..., params=...)` and `http.post(url, json=...)` with auto-JSON parsing to dict/list. Returns `HttpResponse` with `.text`, `.json()`, `.status_code`.
- **Resource pattern** — `resource(fetch_fn)` with `.loading`, `.error`, `.data` states, `.cancel()` and `.retry()` methods, automatic cancellation on screen exit.
- **Lifecycle hooks** — `on_mount`/`on_dispose` for composable enter/exit. `effect(state, callback)` for reactive side effects.
- **Hot Reload** — watch `main.py` for changes, delta-compile only changed composables, preserve UI state.
- **CLI commands** — `laith new`, `laith build`, `laith compile`, `laith run`, `laith doctor`, `laith logs`.
- **Error diagnostics** — `laith doctor` checks JDK, Android SDK, env vars, `laith.toml`. `laith logs` shows filtered Laith logs with Python source references.
- **Project generator** — `laith new myapp` creates complete Android project with navigation, theme, Gradle wrapper, runtime files.
- **Dead code elimination** — unused Python functions, classes, imports removed from generated Kotlin.
- **Source maps** — Python-to-Kotlin mapping for debugging in Android Studio.

[unreleased]: https://github.com/laith/laith/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/laith/laith/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/laith/laith/releases/tag/v0.1.0
