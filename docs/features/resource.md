# Resource Pattern

The `resource` function wraps an async data-fetching operation with built-in loading, error, and retry state management. It maps to a Compose `Resource` sealed class.

## Usage

```python
async def fetch_user() -> str:
    response = await http.get("https://api.example.com/user")
    return response.text

def main_ui():
    user = resource(fetch_user)
    
    if user.loading:
        Text("Loading...")
    elif user.error:
        Column(
            Text(f"Error: {user.error}"),
            Button("Retry", on_click=lambda: user.retry()),
        )
    else:
        Text(f"User: {user.data}")
```

## API

| Property/Method | Type | Description |
|-----------------|------|-------------|
| `.data` | `Any` | The resolved data (once loaded). |
| `.loading` | `bool` | Whether the fetch is in progress. |
| `.error` | `str` | Error message if the fetch failed. |
| `.retry()` | `()` | Retry the fetch operation. |
| `.cancel()` | `()` | Cancel an in-flight fetch. |

## Auto-cancellation

Resources automatically cancel their fetch when the composable leaves composition (via `DisposableEffect`).
