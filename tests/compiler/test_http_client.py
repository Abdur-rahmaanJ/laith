import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestHttpClient:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    resp = http.get("https://example.com")
    Text(resp.text)
""",
            ["HttpURLConnection", "requestMethod"],
            id="get"
        ),
        pytest.param(
            """
def main_ui():
    resp = http.post("https://example.com", json={"key": "value"})
    Text(resp.text)
""",
            ["HttpURLConnection", "requestMethod"],
            id="post"
        ),
        pytest.param(
            """
def main_ui():
    resp = http.get("https://api.example.com")
    data = resp.json()
    Text(data)
""",
            ["json()", "org.json.JSONObject"],
            id="response_json"
        ),
        pytest.param(
            """
def main_ui():
    resp = http.get("https://api.example.com")
    code = resp.status_code
    Text(code)
""",
            ["statusCode"],
            id="response_status_code"
        ),
        pytest.param(
            """
def main_ui():
    resp = http.get("https://api.example.com")
    body = resp.text
    Text(body)
""",
            ["text"],
            id="response_text"
        ),
    ])
    def test_http_client(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
