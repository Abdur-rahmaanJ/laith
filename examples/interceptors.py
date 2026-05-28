"""
Example: HTTP Request/Response Interceptors

Interceptors allow you to hook into HTTP requests and responses globally.
Use cases: adding auth tokens, logging, retry logic.

Usage:
    def add_auth(headers):
        headers["Authorization"] = "Bearer my-token"
        return headers

    http.add_request_interceptor(add_auth)

    def log_response(resp):
        print(f"Got {resp.status_code}")
        return resp

    http.add_response_interceptor(log_response)

    # Now every request goes through the interceptor chain
    resp = http.get("https://api.example.com/data")
"""

def add_auth(headers):
    headers["Authorization"] = "Bearer my-token"
    return headers

def log_response(resp):
    print(f"Got {resp.status_code}")
    return resp

def main_ui():
    http.add_request_interceptor(add_auth)
    http.add_response_interceptor(log_response)
    resp = http.get("https://api.example.com/data")
    Text(resp.text)
