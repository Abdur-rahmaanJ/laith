# Efficient Lists: LazyColumn / LazyRow

LazyColumn and LazyRow provide efficient, scrollable lists that only compose items as they scroll into view. They map to Jetpack Compose's `LazyColumn` and `LazyRow`.

## Usage

### LazyColumn

```python
items = [1, 2, 3, 4, 5]
LazyColumn(
    items=items,
    body=lambda item: Text(f"Item: {item}")
)
```

### LazyRow

```python
items = ["a", "b", "c"]
LazyRow(
    items=items,
    body=lambda item: Button(item, on_click=lambda: print(item))
)
```

## Generated Kotlin

```kotlin
LazyColumn {
    items(items = listOf(1, 2, 3, 4, 5)) { item ->
        Text(text = "Item: ${item}")
    }
}
```
