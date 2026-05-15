# Compiler Error Messages

Laith provides rich, actionable error messages with source context when compilation fails. Every error includes the exact file location, a snippet of the surrounding source code, and a hint for how to fix the issue.

## Error Types

| Error Type | Description |
|------------|-------------|
| `CompileError` | Base error; used for general compilation failures. |
| `TypeError` | Type mismatch (e.g., expected `int` but got `str`). |
| `UndefinedSymbolError` | Reference to a name that does not exist in any visible scope. |
| `UnsupportedFeatureError` | Use of a Python feature that Laith does not yet support. |

## Error Format

Errors are displayed in three parts:

1. **Message**: A short description of what went wrong.
2. **Source context**: 3–5 lines of surrounding Python source with a `>` marker and `^` pointer on the offending line.
3. **Hint**: An actionable suggestion for how to resolve the problem.

### Example

```
Compilation Error: Undefined symbol my_var

    3 | def compute():
    4 |     x = 10
  > 5 |     y = my_var + 1
      |         ^
    6 |     return y

Hint: Did you forget to define my_var or import it?
```

## Programmatic Use

All error types live in `laith.compiler.errors` and can be caught in custom tooling:

```python
from laith.compiler.errors import CompileError, UndefinedSymbolError

try:
    # compilation logic
except CompileError as e:
    print(f"{e.message} at line {e.location.line}")
    if e.hint:
        print(f"Hint: {e.hint}")
```
