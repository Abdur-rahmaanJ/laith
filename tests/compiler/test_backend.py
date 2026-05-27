import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestKotlinEmitterBasic:
    def test_simple_function(self, fresh_analyzer, fresh_emitter):
        code = """
def add_numbers(a: int, b: int) -> int:
    result = a + b
    return result
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "fun addNumbers" in kotlin
        assert "a: Int" in kotlin
        assert "b: Int" in kotlin

    def test_async_function(self, fresh_analyzer, fresh_emitter):
        code = """
async def fetch() -> str:
    return "done"
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "suspend fun fetch" in kotlin
        assert '"done"' in kotlin

    def test_emitter_idempotent(self, fresh_analyzer, fresh_emitter):
        code = """
def f() -> int:
    return 42
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)

        e1 = fresh_emitter.reset().emit(module)
        e2 = fresh_emitter.reset().emit(module)
        assert e1 == e2

    def test_emitter_source_map(self, fresh_analyzer, fresh_emitter):
        code = "def f() -> int:\n    return 42\n"
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        fresh_emitter.reset().emit(module)
        source_map = fresh_emitter.get_source_map()
        assert isinstance(source_map, list)

    def test_state_emission(self, fresh_analyzer, fresh_emitter):
        code = """
def main_ui():
    count = state(0)
    Text(count)
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "mutableStateOf" in kotlin or "MutableStateFlow" in kotlin


class TestKotlinEmitterGolden:
    """Golden snapshot tests for complex emitter outputs."""

    def test_scaffold_output(self, fresh_analyzer, fresh_emitter, golden_dir):
        code = """
def main_ui():
    Scaffold(
        top_bar=TopAppBar(),
        body=Text("Hello"),
    )
"""
        tree = Parser.parse(code)
        scope = fresh_analyzer.analyze(tree)
        builder = IRBuilder(scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        assert "Scaffold" in kotlin
        assert "TopAppBar" in kotlin
        assert "Text" in kotlin

    def test_dialog_output(self, fresh_analyzer, fresh_emitter):
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
