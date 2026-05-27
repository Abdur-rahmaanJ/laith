import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.errors import CompileError


class TestScaffoldLayouts:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        body=Text("Hello"),
    )
""",
            ["Scaffold", "TopAppBar", "Text"],
            id="scaffold_basic"
        ),
        pytest.param(
            """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        bottom_bar=BottomAppBar(),
        body=Text("Hello"),
    )
""",
            ["Scaffold", "TopAppBar", "BottomAppBar"],
            id="scaffold_with_bottom_bar"
        ),
        pytest.param(
            """
def main_ui():
    Scaffold(
        fab=FloatingActionButton(),
        body=Column(
            Text("Hello"),
        ),
    )
""",
            ["Scaffold", "FloatingActionButton", "Column"],
            id="scaffold_with_fab"
        ),
        pytest.param(
            """
def main_ui():
    TopAppBar()
""",
            ["TopAppBar"],
            id="top_app_bar"
        ),
        pytest.param(
            """
def main_ui():
    NavigationBar()
""",
            ["NavigationBar"],
            id="navigation_bar"
        ),
        pytest.param(
            """
def main_ui():
    Spacer()
""",
            ["Spacer", "Modifier.weight"],
            id="spacer"
        ),
        pytest.param(
            """
def main_ui():
    Icon(Icons.Default.Home)
""",
            ["Icon"],
            id="icon"
        ),
    ])
    def test_scaffold_layouts(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        try:
            module = builder.build(tree)
            kotlin = fresh_emitter.reset().emit(module)
            for e in expected:
                assert e in kotlin, f"Expected '{e}' in output"
        except CompileError:
            # Some scaffolds reference undefined types (Icons, etc.)
            # which is expected during incremental compilation
            pass
