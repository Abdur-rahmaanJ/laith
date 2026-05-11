# Kotlin Naming Conventions

Laith automatically converts Python naming conventions to Kotlin conventions when generating source code, making the output readable and idiomatic for Android developers.

## Name Mapping

| Python (snake_case) | Kotlin (camelCase) |
|---------------------|-------------------|
| `my_function` | `myFunction` |
| `fetch_data` | `fetchData` |
| `on_click` | `onClick` |
| `user_name` | `userName` |

## What Gets Converted

- **Function names**: `def calculate_total()` → `fun calculateTotal()`
- **Method names**: `def on_create()` → `fun onCreate()`
- **Keyword arguments**: `on_click=handler` → `onClick = handler`
- **Function call references**: `calculate_total(1, 2)` → `calculateTotal(1, 2)`

## What Stays The Same

- **Class names**: Python classes are already conventionally PascalCase.
- **Field names**: Object fields keep their original names (to match Kotlin property conventions).
- **Parameter variables** emit camelCase forms while preserving the original meaning.

## Source Map Comments

Every generated Kotlin line that maps to a Python source line includes an inline comment:

```kotlin
// from Python line 5
val v_0 = 10 // from Python line 5
```

This enables:
- **Android Studio debugging**: Step through Python-originated code in the Kotlin debugger
- **`laith run` log rewriting**: Crash stack traces are mapped back to Python line numbers
- **Manual inspection**: Developers can trace which Python code generated which Kotlin

## Example

**Python input:**
```python
def calculate_total(price: int, tax_rate: int) -> int:
    tax_amount = price * tax_rate
    total = price + tax_amount
    return total
```

**Generated Kotlin:**
```kotlin
fun calculateTotal(price: Int, taxRate: Int): Int { // from Python: calculate_total
    val v_0 = price * taxRate // from Python line 2
    val v_1 = price + v_0     // from Python line 3
    return v_1                // from Python line 4
}
```
