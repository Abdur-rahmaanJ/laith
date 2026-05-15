# Networking

Laith provides a built-in async HTTP client for making network requests.

## Usage

### GET Request

```python
async def fetch_data():
    response = await http.get("https://api.example.com/data")
    data = response.json()
    return data
```

### POST Request

```python
async def create_item():
    response = await http.post(
        "https://api.example.com/data",
        json={"name": "test", "value": 42},
    )
    return response.status_code
```

### Accessing Response Data

```python
async def fetch():
    resp = await http.get("https://api.example.com/data")
    text = resp.text         # raw text
    status = resp.status_code  # e.g. 200
    data = resp.json()        # parsed JSON dict
```

## Generated Kotlin

GET requests generate OkHttp or `java.net.URL` calls:

```kotlin
suspend fun fetchData(): String {
    val response = httpGet("https://api.example.com/data")
    return response.text
}
```
