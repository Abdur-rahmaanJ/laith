import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestDialogs:
    def test_dialog(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    show = state(True)
    if show:
        Dialog(
            Text("Hello"),
            on_dismiss=lambda: show.set(False),
        )
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "Dialog" in kotlin
        assert "onDismissRequest" in kotlin

    def test_alert_dialog(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    AlertDialog(
        title="Confirm",
        text="Delete?",
        on_confirm=lambda: print("ok"),
        on_dismiss=lambda: print("cancel"),
    )
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "AlertDialog" in kotlin
        assert "confirmButton" in kotlin

    def test_modal_bottom_sheet(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    ModalBottomSheet(
        Text("Content"),
        on_dismiss=lambda: print("dismissed"),
    )
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "ModalBottomSheet" in kotlin

    def test_snackbar(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    Snackbar("Hello")
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "Snackbar" in kotlin


class TestEdgeCases:
    def test_multiple_effects(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    a = state(1)
    b = state(2)
    effect(a, lambda old, new: print(new))
    effect(b, lambda old, new: print(new))
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert kotlin.count("LaunchedEffect") >= 2

    def test_on_mount_twice(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    on_mount(lambda: print("first"))
    on_mount(lambda: print("second"))
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        # Count LaunchedEffect usages in non-import lines
        non_import_lines = [l for l in kotlin.split("\n") if not l.startswith("import ")]
        launched_effect_count = sum(line.count("LaunchedEffect") for line in non_import_lines)
        assert launched_effect_count == 2

    def test_preferences_contains(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    prefs = Preferences("test")
    if prefs.contains("key"):
        Text("found")
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "contains" in kotlin

    def test_theme_no_colors(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    Theme(
        body=Text("Plain"),
    )
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "MaterialTheme" in kotlin

    def test_on_dispose_with_state(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    timer = state(None)
    on_mount(lambda: timer.set("started"))
    on_dispose(lambda: timer.set("stopped"))
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "LaunchedEffect" in kotlin
        assert "DisposableEffect" in kotlin
        assert "onDispose" in kotlin

    def test_file_storage_exists(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    if FileStorage.exists("config.json"):
        Text("config exists")
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "exists" in kotlin

    def test_file_storage_delete(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    if FileStorage.exists("tmp.txt"):
        FileStorage.delete("tmp.txt")
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "delete" in kotlin
