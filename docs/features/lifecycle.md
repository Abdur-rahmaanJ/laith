# Lifecycle & Side Effects

Laith provides composable lifecycle hooks and reactive side effect utilities that bridge to Jetpack Compose's `LaunchedEffect`, `DisposableEffect`, and Android `Lifecycle` APIs.

## Composable Lifecycle

### `on_mount(callback)`

Runs the callback once when the composable enters composition. Maps to `LaunchedEffect(Unit)`.

```python
on_mount(lambda: load_initial_data())
```

### `on_dispose(callback)`

Runs the callback when the composable leaves composition. Maps to `DisposableEffect` + `onDispose`.

```python
on_dispose(lambda: cleanup_resources())
```

## Screen Lifecycle

### `on_resume(callback)`

Runs the callback when the screen resumes (foreground). Maps to `Lifecycle.Event.ON_RESUME` via `LifecycleEventObserver`.

Useful for refreshing data, starting sensors, or resuming media playback.

```python
on_resume(lambda: refresh_feed())
```

### `on_pause(callback)`

Runs the callback when the screen pauses (background). Maps to `Lifecycle.Event.ON_PAUSE`.

Useful for saving drafts, pausing video, or unregistering listeners.

```python
on_pause(lambda: save_draft())
```

## Reactive Side Effects

### `effect(state_var, callback)`

Watches a state variable and calls the callback whenever its value changes. The callback receives `(old_value, new_value)`.

Maps to `LaunchedEffect` with the state variable as the key.

```python
count = state(0)
effect(count, lambda old, new: print(f"Changed: {old} -> {new}"))
Button("Increment", on_click=lambda: count.set(count.value + 1))

# Every time count changes, the effect triggers
```

## Generated Kotlin

**`on_mount`** generates:
```kotlin
LaunchedEffect(Unit) {
    callback()
}
```

**`on_resume`** generates:
```kotlin
val lifecycleOwner = LocalLifecycleOwner.current
DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event ->
        if (event == Lifecycle.Event.ON_RESUME) { callback() }
    }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}
```

**`effect`** generates:
```kotlin
LaunchedEffect(stateVar) {
    val newVal = stateVar
    callback(newVal)
}
```
