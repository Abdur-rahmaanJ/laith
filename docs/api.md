# Laith API Reference

This document provides a comprehensive reference for the Python built-ins, UI components, and decorators supported by the Laith compiler.

## UI Components (Jetpack Compose DSL)

Laith maps these functions directly to high-performance Jetpack Compose primitives.

### `Column(*children, **kwargs)`
A vertical layout that places its children one below the other.
- **Args**: Variable positional arguments for children (Composables).
- **Keywords**: `modifier` (optional).

### `Row(*children, **kwargs)`
A horizontal layout that places its children side by side.
- **Args**: Variable positional arguments for children.

### `Box(*children, **kwargs)`
A stack layout that places children on top of each other.

### `Text(content: str)`
Renders a text label.
- **Example**: `Text(f"Counter: {count.value}")`

### `Button(label: str, on_click: callable)`
A Material3 button.
- **Example**: `Button("Click Me", on_click=lambda: print("Clicked"))`

### `TextField(value: state, on_value_change: callable, label: str = "")`
An outlined text input field with two-way binding.
- **Example**: `TextField(value=text_state, on_value_change=text_state.set, label="Name")`

### `Checkbox(checked: state, on_checked_change: callable)`
A Material3 checkbox with two-way binding.
- **Example**: `Checkbox(checked=agreed_state, on_checked_change=agreed_state.set)`

### `Switch(checked: state, on_checked_change: callable)`
A Material3 toggle switch with two-way binding.
- **Example**: `Switch(checked=enabled_state, on_checked_change=enabled_state.set)`

### `Slider(value: state, on_value_change: callable)`
A Material3 slider with two-way binding.
- **Example**: `Slider(value=volume_state, on_value_change=volume_state.set)`

### `Dialog(*children, on_dismiss: callable)`
A modal dialog overlay.
- **Keywords**: `on_dismiss` (callback when dialog is dismissed).
- **Example**: `Dialog(Text("Hello"), on_dismiss=lambda: close())`

### `AlertDialog(title: str, text: str, on_confirm: callable, on_dismiss: callable)`
A Material3 alert dialog with title, body, and confirm action.
- **Keywords**: `title`, `text`, `on_confirm`, `on_dismiss`.

### `Snackbar(message: str)`
An inline snackbar display.
- **Example**: `Snackbar("Operation complete")`

### `ModalBottomSheet(*children, on_dismiss: callable)`
A modal bottom sheet overlay.
- **Keywords**: `on_dismiss` (callback when sheet is dismissed).

---

## Layout & Structure

### `Scaffold(top_bar=..., bottom_bar=..., fab=..., body=...)`
Standard Material3 screen structure with top bar, bottom bar, floating action button, and body content.
- **Keywords**: `top_bar` (TopAppBar), `bottom_bar` (BottomAppBar/NavigationBar), `fab` (FloatingActionButton), `body` (content composable)

### `TopAppBar()`
A Material3 top app bar.

### `BottomAppBar()`
A Material3 bottom app bar.

### `NavigationBar(*items)`
A Material3 bottom navigation bar.

### `NavigationBarItem()`
An item inside a NavigationBar.

### `FloatingActionButton(on_click: callable, *children)`
A circular Material3 button for primary actions.

### `Spacer()`
A flexible spacer that pushes siblings apart (uses `Modifier.weight(1f)`).

### `Icon(icon)`
A Material3 icon.
- **Example**: `Icon(Icons.Default.Home)`

### `Image(src: str)`
An image composable.
- **Example**: `Image("https://example.com/photo.png")`

### `LazyColumn(items: list, body: callable)`
An efficient vertically scrolling list that only composes visible items.
- **Keywords**: `items` (iterable of data), `body` (lambda receiving each item).
- **Example**: `LazyColumn(items=[1,2,3], body=lambda item: Text(item))`

### `LazyRow(items: list, body: callable)`
An efficient horizontally scrolling list.
- **Keywords**: `items` (iterable of data), `body` (lambda receiving each item).
- **Example**: `LazyRow(items=["a","b"], body=lambda item: Button(item, on_click=...))`

---

## Navigation

### `Navigator.push(screen, **params)`
Pushes a screen onto the navigation stack.
- `screen`: Reference to a screen function.
- `**params`: Keyword arguments passed as navigation parameters.
- **Example**: `Navigator.push(profile, user_id=42)`

### `Navigator.pop(result=None)`
Pops the current screen from the navigation stack, optionally returning a result.
- **Example**: `Navigator.pop("confirmed")`

### `@route(path="/screen")`
Decorator to register a screen function with a navigation route path for deep linking.
- **Example**: `@route(path="/profile/:id")`

---

## Theming

### `Theme(primary: str, dark_primary: str, use_dynamic_colors: bool, body=...)`
Wraps content in a MaterialTheme with customizable colors and dark mode support.
- **Keywords**: 
  - `primary` (hex color for light theme, e.g. `"#FF6200EE"`)
  - `dark_primary` (hex color for dark theme, e.g. `"#FFBB86FC"`)
  - `use_dynamic_colors` (Android 12+ Monet palette)
  - `body` (content composable)
- **Example**: 
```python
Theme(
    primary="#FF6200EE",
    dark_primary="#FFBB86FC",
    body=Column(
        Text("Themed Content")
    )
)
```

---

## Dynamic SDK Bridge

Laith provides automatic resolution of Android SDK classes. When you use an undefined identifier, the compiler searches common Android packages and resolves it to the fully qualified class name.

### Auto-Resolved Classes

| Python Identifier | Resolved Android Class |
|-------------------|----------------------|
| `Intent` | `android.content.Intent` |
| `Uri` | `android.net.Uri` |
| `Context` | `android.content.Context` |
| `context` | Pre-defined as `android.content.Context` (built-in variable) |
| `Build` | `android.os.Build` |
| `Toast` | `android.widget.Toast` |
| `Environment` | `android.os.Environment` |
| `BatteryManager` | `android.os.BatteryManager` |
| `Sensor` | `android.hardware.Sensor` |
| `SensorManager` | `android.hardware.SensorManager` |

### System Intents Example

```python
from laith import Column, Text, Button

def open_docs():
    url = "https://laith.dev"
    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    context.startActivity(intent)

def main_ui():
    Column(
        Text("Laith Intent Lab"),
        Button("Visit Documentation", on_click=lambda: open_docs())
    )
```

The `context` variable is a built-in that provides access to the Activity context, enabling direct Android API calls.

---

## Android Interop

### `AndroidView(factory=lambda: ...)`

Embeds an arbitrary Android View inside the Compose UI tree. Enables use of Maps, ExoPlayer, WebView, and any third-party Android view library.

- **Args**: First positional arg is a factory lambda that receives an Android `Context` and returns a `View`.
- **Example**:
```python
def main_ui():
    AndroidView(factory=lambda: context)
```

### `KotlinComposable("fully.qualified.Name", arg1=val1, ...)`

Calls any Jetpack Compose composable function by its fully-qualified Kotlin name. Enables gradual migration — write screens in Kotlin, call them from Laith.

- **Args**: First positional arg is the fully-qualified composable function name (string). Remaining keyword args are passed as parameters.
- **Example**:
```python
def main_ui():
    KotlinComposable("com.example.MyScreen", title="Hello", count=42)
```

---

## Runtime Permissions

### `@requires_permission(permission)`

Decorator that marks a function as requiring a specific Android permission. The compiler automatically:
1. Adds the permission to `AndroidManifest.xml`
2. Generates a runtime `checkSelfPermission` call at the function start

- **Example**:
```python
@requires_permission("CAMERA")
def take_photo():
    # This function only runs if CAMERA permission is granted
    pass
```

### `remember_permission(permission)`

A composable that returns a reactive permission state object.

- **Properties**:
    - `.granted` → Boolean indicating if permission is granted.
    - `.should_show_rationale` → Boolean indicating if rationale should be shown (after denial).
    - `.request()` → Triggers the runtime permission dialog.
- **Example**:
```python
def main_ui():
    cam = remember_permission("CAMERA")
    if cam.granted:
        Text("Camera available")
    else:
        Button("Request Camera", on_click=lambda: cam.request())
```

---

## Crash Overlay (Development)

Laith wraps all UI content in a `CrashOverlay` error boundary. When an uncaught exception occurs during composition, a full-screen overlay appears with:
- Error message and stack trace
- "Reload App" button that restarts the Activity

No manual setup is required — the crash overlay is automatically active in every Laith project.

---

## State Management

### `state(initial_value: Any)`
Creates a reactive state variable. In UI functions, this maps to `MutableState`; in global/class scopes, it maps to `MutableStateFlow`.
- **Methods**:
    - `.value`: Retrieves the current value (reactive in UI).
    - `.set(new_value)`: Updates the value and triggers recomposition.

---

## Hardware & System Built-ins

### `vibrate(ms: int)`
Triggers the device vibrator for the specified duration.
- **Infers**: `android.permission.VIBRATE`.

### `get_location(callback: callable)`
Retrieves the last known GPS location or requests a fresh one.
- **Callback**: `lambda lat, lon: ...`
- **Infers**: `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`.

### `request_location_permission(callback: callable)`
Triggers a system dialog to request location permissions.
- **Callback**: `lambda granted: ...` (Boolean).

### `has_permission(permission: str) -> bool`
Checks if the application currently holds the specified Android permission.

---

## Background & Performance Decorators

### `@native`
Marks a function for compilation to native C++ via the NDK. The function body must follow the C++ subset supported by the `CPPEmitter`.

### `@periodic_task(interval_minutes: int)`
Schedules the function to run in the background using Android `WorkManager`.

### `@foreground_service`
Marks a function to run as a persistent Android Foreground Service.

---

## Networking

### `http` (Async HTTP Client)

A built-in variable providing async HTTP methods. All methods are `async` (must be `await`ed).

- **Methods**:
    - `await http.get(url)` → GET request, returns `HttpResponse`.
    - `await http.post(url, json=dict)` → POST request with optional JSON body.
    - `await http.download(url, local_path, on_progress=...)` → Download a file to disk with progress callbacks.
    - `await http.upload(url, local_path, on_progress=...)` → Upload a file from disk with progress callbacks.
    - `http.add_request_interceptor(func)` → Register a request interceptor that modifies headers.
    - `http.add_response_interceptor(func)` → Register a response interceptor that transforms responses.

### `HttpResponse`

Returned by `http.get()` / `http.post()`.

- **Properties/Methods**:
    - `.text` → Response body as a string.
    - `.status_code` → HTTP status code (int).
    - `.json()` → Parse response body as JSON (returns dict).

- **Example**:
```python
async def fetch_data():
    response = await http.get("https://api.example.com/data")
    data = response.json()
    return data

async def create_item():
    response = await http.post("https://api.example.com/data", json={"name": "test"})
    return response.status_code
```

---

## Asynchronous UI State

### `resource(async_fn)`
Creates a resource wrapper around an async data-fetching function with loading/error/retry support.
- **Argument**: A reference to an `async` function (passed by name, not called).
- **Properties/Methods**:
    - `.data` → The resolved data once loaded.
    - `.loading` → Boolean indicating if the resource is currently loading.
    - `.retry()` → Retry fetching the resource.
    - `.cancel()` → Cancel an in-flight fetch.
- **Example**:
```python
async def fetch_user() -> str:
    return await http.get("https://api.example.com/user")

def main_ui():
    user = resource(fetch_user)
    if user.loading:
        Text("Loading...")
    else:
        Text(f"User: {user.data}")
        Button("Retry", on_click=lambda: user.retry())
```

---

## IPC & Communication

### `Channel()`
Creates an asynchronous communication channel for event-driven logic between UI and background layers.
- **Methods**:
    - `.send(value)`: Sends a message into the channel.
    - `.collect(callback)`: Subscribes to messages.

---

## Lifecycle Hooks

### `on_mount(callback)`
Runs the callback when the composable enters composition (maps to `LaunchedEffect(Unit)`).
- **Example**: `on_mount(lambda: load_data())`

### `on_dispose(callback)`
Runs the callback when the composable leaves composition (maps to `DisposableEffect` + `onDispose`).
- **Example**: `on_dispose(lambda: cleanup())`

### `on_resume(callback)`
Runs the callback when the screen resumes (maps to `Lifecycle.Event.ON_RESUME` observer).
- **Example**: `on_resume(lambda: refresh_data())`

### `on_pause(callback)`
Runs the callback when the screen pauses (maps to `Lifecycle.Event.ON_PAUSE` observer).
- **Example**: `on_pause(lambda: save_draft())`

### `effect(state_var, callback)`
Watches a state variable and calls the callback with the new value whenever it changes (maps to `LaunchedEffect` with the state as key).
- **Example**: `effect(count, lambda old, new: print(f"Count changed from {old} to {new}"))`

---

## Storage & Persistence

### `Preferences(name: str)`
Creates a SharedPreferences-backed key-value store.
- **Methods**:
    - `get(key, default)`: Retrieves a value or returns the default.
    - `set(key, value)`: Stores a value.
    - `remove(key)`: Deletes a key.
    - `contains(key)`: Checks if a key exists.
- **Example**:
```python
prefs = Preferences("my_app")
name = prefs.get("username", "guest")
prefs.set("username", "new_name")
```

### `FileStorage`
Static utility class for raw file I/O in the app's internal storage.
- **Static methods**:
    - `read_text(path)` → Reads a text file from internal storage.
    - `write_text(path, data)` → Writes text to a file.
    - `read_bytes(path)` → Reads binary data from a file.
    - `write_bytes(path, data)` → Writes binary data to a file.
    - `delete(path)` → Deletes a file.
    - `exists(path)` → Checks if a file exists.
    - `get_cache_dir()` → Returns the cache directory path.
    - `get_files_dir()` → Returns the files directory path.
- **Example**:
```python
content = FileStorage.read_text("notes.txt")
FileStorage.write_bytes("backup.bin", data)
cache = FileStorage.get_cache_dir()
```

### `Database(name: str)`
Creates a SQLite database connection backed by Android's `SQLiteOpenHelper`.
- **Methods**:
    - `query(sql, *params)` → Executes a SELECT query with optional bind params.
    - `execute(sql, *params)` → Executes a statement (INSERT, CREATE, etc.).
    - `close()` → Closes the database connection.
- **Example**:
```python
db = Database("app.db")
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
db.execute("INSERT INTO users (name) VALUES (?)", "Alice")
users = db.query("SELECT * FROM users WHERE id = ?", 1)
db.close()
```

### `SecureStorage(name: str)`
Creates an encrypted key-value store backed by `EncryptedSharedPreferences`.
- **Methods**:
    - `get(key)` → Retrieves an encrypted string value.
    - `set(key, value)` → Stores an encrypted string value.
    - `remove(key)` → Deletes a key.
    - `contains(key)` → Checks if a key exists.
- **Example**:
```python
vault = SecureStorage("secrets")
vault.set("token", "abc123")
token = vault.get("token")
```
