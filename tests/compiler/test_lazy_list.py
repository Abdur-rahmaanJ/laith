import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestLazyComponents:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    LazyColumn(items=["a", "b"], body=lambda item: Text(item))
""",
            ["LazyColumn", "items"],
            id="lazy_column_basic"
        ),
        pytest.param(
            """
def main_ui():
    LazyColumn(items=[], body=lambda item: Text(item))
""",
            ["LazyColumn", "items"],
            id="lazy_column_empty"
        ),
        pytest.param(
            """
def main_ui():
    LazyRow(items=["a", "b"], body=lambda item: Text(item))
""",
            ["LazyRow", "items"],
            id="lazy_row_basic"
        ),
        pytest.param(
            """
def main_ui():
    LazyRow(items=[], body=lambda item: Text(item))
""",
            ["LazyRow"],
            id="lazy_row_is_composable"
        ),
    ])
    def test_lazy_components(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
