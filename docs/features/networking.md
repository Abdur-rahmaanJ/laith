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

### File Download

Download a file to local storage with optional progress tracking:

```python
async def download_file():
    await http.download(
        "https://example.com/photo.jpg",
        "/storage/photos/photo.jpg",
        on_progress=lambda pct: print(f"Download: {pct}%")
    )
```

### File Upload

Upload a file from local storage:

```python
async def upload_file():
    await http.upload(
        "https://api.example.com/upload",
        "/storage/tmp/report.pdf",
        on_progress=lambda pct: print(f"Upload: {pct}%")
    )
```

### Request Interceptors

Register a function that modifies every outgoing request's headers:

```python
def add_auth_token(headers):
    headers["Authorization"] = "Bearer my-token"
    return headers

http.add_request_interceptor(add_auth_token)
```

### Response Interceptors

Register a function that transforms every incoming response:

```python
def log_response(resp):
    print(f"Got {resp.status_code} from {resp.url}")
    return resp

http.add_response_interceptor(log_response)
```

## Generated Kotlin

GET requests generate OkHttp or `java.net.URL` calls:

```kotlin
suspend fun fetchData(): String {
    val response = httpGet("https://api.example.com/data")
    return response.text
}
```

Interceptors are stored in mutable lists and applied in order before/after each HTTP call:

```kotlin
val requestInterceptors = mutableListOf<(Map<String, String>) -> Map<String, String>>()
val responseInterceptors = mutableListOf<(HttpResponse) -> HttpResponse>()
```
