# Storage & Persistence

Laith provides two storage APIs for persisting data: `Preferences` for key-value pairs and `FileStorage` for raw file I/O.

## Preferences (Key-Value Store)

Backed by Android `SharedPreferences`. Ideal for settings, user preferences, and small amounts of structured data.

### Creating a Preferences Instance

```python
prefs = Preferences("my_app_name")
```

### Methods

| Method | Description |
|--------|-------------|
| `get(key, default)` | Retrieves a string value or returns the default. |
| `set(key, value)` | Stores a string value. |
| `remove(key)` | Deletes a key. |
| `contains(key)` | Checks if a key exists (returns `Boolean`). |

### Example

```python
def main_ui():
    prefs = Preferences("todo_app")
    saved_name = prefs.get("username", "guest")

    Column(
        Text(f"Welcome, {saved_name}"),
        Button("Save", on_click=lambda: prefs.set("username", "Alice")),
        Button("Clear", on_click=lambda: prefs.remove("username")),
    )
```

## FileStorage (Raw File I/O)

Backed by `java.io.File` in the app's internal storage (`context.filesDir` / `context.cacheDir`). Ideal for logs, exports, images, and binary data.

### Static Methods

| Method | Description |
|--------|-------------|
| `read_text(path)` | Reads a text file from internal storage. |
| `write_text(path, data)` | Writes text to a file. |
| `read_bytes(path)` | Reads binary data from a file. |
| `write_bytes(path, data)` | Writes binary data to a file. |
| `delete(path)` | Deletes a file. |
| `exists(path)` | Checks if a file exists. |
| `get_cache_dir()` | Returns the absolute path to the cache directory. |
| `get_files_dir()` | Returns the absolute path to the files directory. |

### Example

```python
def main_ui():
    FileStorage.write_text("log.txt", "App started")
    content = FileStorage.read_text("log.txt")
    cache_path = FileStorage.get_cache_dir()
    has_file = FileStorage.exists("config.json")

    Text(f"Log: {content}")
```

## Generated Kotlin

**Preferences** generates:
```kotlin
val prefs = context.getSharedPreferences("my_app_name", Context.MODE_PRIVATE)
val savedName = prefs.getString("username", "guest") ?: "guest"
prefs.edit().putString("username", "Alice").apply()
```

**FileStorage** generates:
```kotlin
java.io.File(context.filesDir, "log.txt").writeText("App started")
val content = java.io.File(context.filesDir, "log.txt").readText()
val cachePath = context.cacheDir.absolutePath
```
