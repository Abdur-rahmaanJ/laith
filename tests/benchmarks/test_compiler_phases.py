from __future__ import annotations
import pytest
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.optimizer.base import Optimizer
from laith.compiler.optimizer.const_fold import ConstantFoldingPass
from laith.compiler.optimizer.dce import DCEPass


SIMPLE_SOURCE = """
def add(a: int, b: int) -> int:
    return a + b

def main():
    x = add(1, 2)
    return x
"""


class TestCompilerPhaseTiming:
    """Measure per-phase compilation time."""

    def test_parse_phase(self, benchmark):
        def parse():
            Parser.parse(SIMPLE_SOURCE)
        benchmark.measure("parse", parse)

    def test_analyze_phase(self, benchmark):
        tree = Parser.parse(SIMPLE_SOURCE)

        def analyze():
            SemanticAnalyzer().analyze(tree)
        benchmark.measure("analyze", analyze, warmup=5)

    def test_ir_build_phase(self, benchmark):
        tree = Parser.parse(SIMPLE_SOURCE)
        scope = SemanticAnalyzer().analyze(tree)

        def build_ir():
            IRBuilder(scope).build(tree)
        benchmark.measure("build_ir", build_ir, warmup=5)

    def test_optimize_phase(self, benchmark):
        tree = Parser.parse(SIMPLE_SOURCE)
        scope = SemanticAnalyzer().analyze(tree)
        module = IRBuilder(scope).build(tree)

        def optimize():
            m = __import__("copy").deepcopy(module)
            opt = Optimizer()
            opt.add_pass(ConstantFoldingPass())
            opt.add_pass(DCEPass())
            opt.optimize(m)
        benchmark.measure("optimize", optimize, warmup=5)

    def test_emit_kotlin_phase(self, benchmark):
        tree = Parser.parse(SIMPLE_SOURCE)
        scope = SemanticAnalyzer().analyze(tree)
        module = IRBuilder(scope).build(tree)

        def emit():
            KotlinEmitter().reset().emit(module)
        benchmark.measure("emit_kotlin", emit, warmup=5)


class TestFullPipelineTiming:
    """Measure end-to-end compilation time."""

    def test_full_pipeline(self, benchmark):
        def full_compile():
            tree = Parser.parse(SIMPLE_SOURCE)
            scope = SemanticAnalyzer().analyze(tree)
            module = IRBuilder(scope).build(tree)
            opt = Optimizer()
            opt.add_pass(ConstantFoldingPass())
            opt.add_pass(DCEPass())
            opt.optimize(module)
            KotlinEmitter().reset().emit(module)
        benchmark.measure("full_pipeline", full_compile, warmup=5)


class TestEmitterTiming:
    """Measure emitter performance with various input sizes."""

    @pytest.mark.parametrize("size,func_count", [
        ("small", 1),
        ("medium", 10),
        ("large", 50),
    ])
    def test_emitter_scaling(self, benchmark, size, func_count):
        funcs = []
        for i in range(func_count):
            funcs.append(f"""
def func_{i}() -> int:
    x = {i}
    y = x + 1
    return y
""")
        source = "\n".join(funcs)
        tree = Parser.parse(source)
        scope = SemanticAnalyzer().analyze(tree)
        module = IRBuilder(scope).build(tree)

        def emit():
            KotlinEmitter().reset().emit(module)
        benchmark.measure(f"emit_{size}_{func_count}funcs", emit, warmup=3)
