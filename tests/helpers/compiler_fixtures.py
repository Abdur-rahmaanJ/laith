from __future__ import annotations
from typing import Callable
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.backend.native.emitter import CPPEmitter
from laith.compiler.ir.nodes import IRModule


class CompilePipeline:
    """Lazy compilation pipeline factory.

    Constructs compiler components on demand and provides
    a clean interface for the most common test patterns.
    """

    def compile(self, source: str, backend: str = "kotlin") -> str:
        tree = Parser.parse(source)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        module = builder.build(tree)
        if backend == "kotlin":
            return KotlinEmitter().reset().emit(module)
        elif backend == "cpp":
            return CPPEmitter().emit(module)
        raise ValueError(f"Unknown backend: {backend}")

    def compile_to_ir(self, source: str) -> IRModule:
        tree = Parser.parse(source)
        analyzer = SemanticAnalyzer()
        global_scope = analyzer.analyze(tree)
        builder = IRBuilder(global_scope)
        return builder.build(tree)

    def compile_to_kotlin(self, source: str) -> str:
        return self.compile(source, backend="kotlin")

    def compile_to_cpp(self, source: str) -> str:
        return self.compile(source, backend="cpp")


def compile_source(source: str, parser, analyzer, emitter) -> str:
    """Legacy compatibility shim."""
    tree = parser.parse(source)
    global_scope = analyzer.reset().analyze(tree)
    builder = IRBuilder(global_scope)
    module = builder.build(tree)
    return emitter.reset().emit(module)
