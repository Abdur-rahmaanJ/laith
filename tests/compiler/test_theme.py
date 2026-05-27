import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestTheme:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    Theme()
""",
            ["MaterialTheme"],
            id="basic"
        ),
        pytest.param(
            """
def main_ui():
    Theme(
        primary="#FF6200EE",
        body=Text("Styled"),
    )
""",
            ["MaterialTheme", "lightColorScheme", "primary"],
            id="with_colors"
        ),
        pytest.param(
            """
def main_ui():
    Theme(
        primary="#FF6200EE",
        dark_primary="#FFBB86FC",
        body=Text("Styled"),
    )
""",
            ["MaterialTheme", "lightColorScheme", "darkColorScheme"],
            id="dark_light"
        ),
        pytest.param(
            """
def main_ui():
    Theme(
        use_dynamic_colors=True,
        body=Text("Dynamic"),
    )
""",
            ["dynamicLightColorScheme", "dynamicDarkColorScheme"],
            id="dynamic_colors"
        ),
        pytest.param(
            """
def main_ui():
    Theme(
        body=Text("Hello"),
    )
""",
            ["MaterialTheme"],
            id="is_composable"
        ),
    ])
    def test_theme(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
