import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter


class TestReleaseBuilds:
    def test_import_deduplication(self, fresh_emitter):
        code = """
def main_ui():
    Text("Hello")
    Button("Click")
    Column(
        Text("Nested"),
    )
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        import_lines = [l for l in kotlin.split("\n") if l.startswith("import ")]
        unique_imports = set(import_lines)
        assert len(import_lines) == len(unique_imports), f"Duplicate imports: {len(import_lines)} vs {len(unique_imports)} unique"

    def test_emitter_output_well_formed(self, fresh_emitter):
        code = """
def main_ui():
    Column(
        Text("Hello"),
        Button("Click"),
    )
"""
        tree = Parser.parse(code)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        kotlin = fresh_emitter.reset().emit(module)

        lines = kotlin.split("\n")
        brace_count = 0
        for line in lines:
            brace_count += line.count("{")
            brace_count -= line.count("}")
        assert brace_count == 0, f"Mismatched braces: {brace_count}"
