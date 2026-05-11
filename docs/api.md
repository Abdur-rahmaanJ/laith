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

---

## Dynamic SDK Bridge

Laith provides automatic resolution of Android SDK classes. When you use an undefined identifier, the compiler searches common Android packages and resolves it to the fully qualified class name.

### Auto-Resolved Classes

The following Android classes are automatically resolved at compile-time:

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
    # Intent and Uri are auto-resolved to android.content.Intent and android.net.Uri
    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    context.startActivity(intent)

def main_ui():
    Column(
        Text("Laith Intent Lab"),
        Text("Click the button below to open the official documentation."),
        Button("Visit Documentation", on_click=lambda: open_docs())
    )
```

The `context` variable is a built-in that provides access to the Activity context, enabling direct Android API calls.

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

## IPC & Communication

### `Channel()`
Creates an asynchronous communication channel for event-driven logic between UI and background layers.
- **Methods**:
    - `.send(value)`: Sends a message into the channel.
    - `.collect(callback)`: Subscribes to messages.
