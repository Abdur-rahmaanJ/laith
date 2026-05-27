import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestInputWidgets:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    TextField(value="hello", on_value_change=lambda v: print(v))
""",
            ["OutlinedTextField", "onValueChange"],
            id="textfield"
        ),
        pytest.param(
            """
def main_ui():
    TextField(value="hello", label="Name", on_value_change=lambda v: print(v))
""",
            ["OutlinedTextField"],
            id="textfield_label"
        ),
        pytest.param(
            """
def main_ui():
    Checkbox(checked=True, on_checked_change=lambda v: print(v))
""",
            ["Checkbox", "onCheckedChange"],
            id="checkbox"
        ),
        pytest.param(
            """
def main_ui():
    Switch(checked=True, on_checked_change=lambda v: print(v))
""",
            ["Switch", "onCheckedChange"],
            id="switch"
        ),
        pytest.param(
            """
def main_ui():
    Slider(value=0.5, on_value_change=lambda v: print(v))
""",
            ["Slider", "onValueChange"],
            id="slider"
        ),
        pytest.param(
            """
def main_ui():
    TextField(value="a", on_value_change=lambda v: print(v))
    Checkbox(checked=False, on_checked_change=lambda v: print(v))
    Switch(checked=True, on_checked_change=lambda v: print(v))
    Slider(value=0.5, on_value_change=lambda v: print(v))
""",
            ["OutlinedTextField", "Checkbox", "Switch", "Slider"],
            id="all_widgets"
        ),
    ])
    def test_input_widgets(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
