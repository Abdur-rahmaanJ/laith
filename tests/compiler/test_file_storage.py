import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestFileStorage:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    data = FileStorage.read_text("config.json")
""",
            ["readText"],
            id="read_text"
        ),
        pytest.param(
            """
def main_ui():
    FileStorage.write_text("backup.json", "data")
""",
            ["writeText"],
            id="write_text"
        ),
        pytest.param(
            """
def main_ui():
    FileStorage.write_bytes("data.bin", b"bytes")
""",
            ["writeBytes"],
            id="write_bytes"
        ),
        pytest.param(
            """
def main_ui():
    if FileStorage.exists("config.json"):
        Text("found")
""",
            ["exists"],
            id="exists"
        ),
        pytest.param(
            """
def main_ui():
    FileStorage.delete("tmp.txt")
""",
            ["delete"],
            id="delete"
        ),
        pytest.param(
            """
def main_ui():
    dir = FileStorage.get_cache_dir()
    Text(dir)
""",
            ["cacheDir"],
            id="get_cache_dir"
        ),
    ])
    def test_file_storage(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
