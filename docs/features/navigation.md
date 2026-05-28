# Navigation

Laith provides a stack-based navigator for managing screen transitions in your app. The navigator maps to Jetpack Compose Navigation under the hood.

## `Navigator` API

### `Navigator.push(screen, **params)`

Navigates to a new screen, pushing it onto the navigation stack.

- `screen`: A reference to the screen function to navigate to.
- `**params`: Keyword arguments passed as navigation arguments.

```python
def settings():
    Text("Settings Screen")

def main_ui():
    Button("Open Settings", on_click=lambda: Navigator.push(settings))
```

### `Navigator.pop(result=None)`

Pops the current screen from the navigation stack, optionally returning a result.

```python
def confirm_dialog():
    Button("Confirm", on_click=lambda: Navigator.pop("confirmed"))

def main_ui():
    Button("Show Dialog", on_click=lambda: Navigator.push(confirm_dialog))
```

## Screen Registration with `@route`

Use the `@route` decorator to register a screen with a specific path, scheme, and host for deep linking:

```python
@route(path="/profile")
def profile_screen():
    Text("Profile")

@route(path="/settings/:section")
def settings_screen(section: str):
    Text(f"Settings: {section}")

@route(path="/item/:id", scheme="myapp", host="example.com")
def item_detail(item: str):
    Text(f"Item: {item}")
```

The compiler generates:
- `NavHost` `deepLinks` entries for each registered route
- `<intent-filter>` entries in `AndroidManifest.xml` for external deep links
- `singleTask` launch mode and `onNewIntent` handling for proper deep link dispatch

## Generated Kotlin

The compiler generates navigation infrastructure including:

- `LaithNavHost`: A composable that sets up `NavHost` with all registered routes.
- `navigatorPush()` / `navigatorPop()`: Helper functions for programmatic navigation.
- `@Route` annotations on composable functions corresponding to Python `@route` decorators.

## Example

```python
from laith import Column, Text, Button, Navigator

@route(path="/home")
def home():
    Column(
        Text("Home Screen"),
        Button("Go to Profile", on_click=lambda: Navigator.push(profile, user_id=42)),
    )

@route(path="/profile")
def profile():
    Column(
        Text("Profile Screen"),
        Button("Back", on_click=lambda: Navigator.pop()),
    )
```
