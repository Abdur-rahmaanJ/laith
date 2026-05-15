# Theming

Laith provides a `Theme` composable that wraps your app content in a Material3 `MaterialTheme` with support for light/dark color schemes and Android 12+ dynamic colors (Monet).

## Usage

### Basic Theme

```python
Theme(
    body=Column(
        Text("Hello, Themed World!"),
        Button("Click", on_click=lambda: print("clicked")),
    )
)
```

### Custom Colors

```python
Theme(
    primary="#FF6200EE",
    dark_primary="#FFBB86FC",
    body=Text("Styled Content"),
)
```

- `primary` sets the light theme primary color (hex).
- `dark_primary` sets the dark theme primary color. Falls back to `primary` if not specified.
- The compiler generates `lightColorScheme` / `darkColorScheme` with an `isSystemInDarkTheme()` check.

### Dynamic Colors (Android 12+)

```python
Theme(
    use_dynamic_colors=True,
    body=Text("Adaptive colors based on wallpaper"),
)
```

- When `use_dynamic_colors` is `True`, the compiler generates `dynamicLightColorScheme` / `dynamicDarkColorScheme` from `LocalContext.current`.
- Falls back gracefully on older Android versions.

### Composing with Scaffold

```python
Theme(
    primary="#FF6200EE",
    body=Scaffold(
        top_bar=TopAppBar(),
        body=Column(
            Text("Content"),
        ),
    ),
)
```

## Generated Kotlin

A `Theme(primary="#FF6200EE", dark_primary="#FFBB86FC", body=...)` call generates:

```kotlin
MaterialTheme(
    colorScheme = if (isSystemInDarkTheme()) {
        darkColorScheme(primary = Color(0xFFFFBB86FC))
    } else {
        lightColorScheme(primary = Color(0xFFFF6200EE))
    }
) {
    // body content
}
```
