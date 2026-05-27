import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestDialogs:
    @pytest.mark.parametrize("code,expected", [
        pytest.param(
            """
def main_ui():
    show = state(True)
    if show:
        Dialog(
            Text("Hello"),
            on_dismiss=lambda: show.set(False),
        )
""",
            ["Dialog", "onDismissRequest"],
            id="dialog"
        ),
        pytest.param(
            """
def main_ui():
    AlertDialog(
        title="Confirm",
        text="Delete?",
        on_confirm=lambda: print("ok"),
        on_dismiss=lambda: print("cancel"),
    )
""",
            ["AlertDialog", "confirmButton"],
            id="alert_dialog"
        ),
        pytest.param(
            """
def main_ui():
    ModalBottomSheet(
        Text("Content"),
        on_dismiss=lambda: print("dismissed"),
    )
""",
            ["ModalBottomSheet"],
            id="modal_bottom_sheet"
        ),
        pytest.param(
            """
def main_ui():
    Snackbar("Hello")
""",
            ["Snackbar"],
            id="snackbar"
        ),
        pytest.param(
            """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        body=Column(
            Dialog(
                Text("Inner"),
                on_dismiss=lambda: print("dismissed"),
            ),
        ),
    )
""",
            ["Dialog", "Scaffold"],
            id="dialog_in_scaffold"
        ),
    ])
    def test_dialogs(self, code, expected, fresh_emitter):
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        for e in expected:
            assert e in kotlin, f"Expected '{e}' in output"
