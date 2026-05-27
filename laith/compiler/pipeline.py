from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

from laith.compiler.cache import CacheStore, ArtifactKey
from laith.compiler.frontend.analyzer import Parser, SemanticAnalyzer
from laith.compiler.ir.builder import IRBuilder
from laith.compiler.ir.nodes import IRModule
from laith.compiler.backend.kotlin.emitter import KotlinEmitter
from laith.compiler.backend.native.emitter import CPPEmitter
from laith.compiler.optimizer.base import Optimizer
from laith.compiler.optimizer.const_fold import ConstantFoldingPass
from laith.compiler.optimizer.dce import DCEPass
from laith.compiler.optimizer.inliner import InlinerPass


@dataclass
class SourceFile:
    path: Path
    content: str
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = hashlib.sha256(self.content.encode()).hexdigest()


@dataclass
class BuildInput:
    sources: Dict[str, SourceFile]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildOutput:
    kotlin: Optional[str] = None
    cpp: Optional[str] = None
    jni: Optional[str] = None
    errors: list = field(default_factory=list)
    cache_hits: Dict[str, str] = field(default_factory=dict)


def serialize_ast(tree) -> bytes:
    import ast as ast_module
    return ast_module.dump(tree, indent=None).encode()


def deserialize_ast(data: bytes):
    import ast as ast_module
    return ast_module.parse("")  # Placeholder


def serialize_ir(module: IRModule) -> bytes:
    return repr(module).encode()


def deserialize_ir(data: bytes) -> IRModule:
    raise NotImplementedError("IR deserialization from repr not yet implemented")


class IncrementalCompiler:
    def __init__(self, cache: CacheStore):
        self._cache = cache
        self._stats = {"cache_hits": 0, "cache_misses": 0}

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def compile(self, inp: BuildInput, phase: str = "all") -> BuildOutput:
        out = BuildOutput()

        ast_results = {}
        for name, src in inp.sources.items():
            key = ArtifactKey.from_source(src.content, "parse")
            cached = self._cache.get(key)
            if cached:
                ast = deserialize_ast(cached)
                out.cache_hits["parse"] = key.source_hash
                self._stats["cache_hits"] += 1
            else:
                tree = Parser.parse(src.content)
                self._cache.set(key, serialize_ast(tree))
                ast_results[name] = tree
                self._stats["cache_misses"] += 1

        if phase == "parse":
            return out

        if not ast_results:
            primary_src = list(inp.sources.values())[0]
            key = ArtifactKey.from_source(primary_src.content, "parse")
            cached = self._cache.get(key)
            if cached:
                ast_results[primary_src.path.name] = deserialize_ast(cached)

        combined_hash = hashlib.sha256(
            "".join(sorted(
                hashlib.sha256(repr(tree).encode()).hexdigest()
                for tree in ast_results.values()
            )).encode()
        ).hexdigest()

        ir_key = ArtifactKey(
            source_hash=combined_hash,
            phase="build_ir",
            options_hash="",
        )
        ir_cached = self._cache.get(ir_key)
        if ir_cached:
            module = deserialize_ir(ir_cached)
            out.cache_hits["ir"] = ir_key.source_hash
        else:
            primary_tree = list(ast_results.values())[0]
            scope = SemanticAnalyzer().analyze(primary_tree)
            module = IRBuilder(scope).build(primary_tree)
            self._cache.set(ir_key, serialize_ir(module))

        if phase in ("ir", "analyze"):
            return out

        optimizer = Optimizer()
        for pass_cls_name, pass_cls in [
            ("const_fold", ConstantFoldingPass),
            ("dce", DCEPass),
            ("inliner", InlinerPass),
        ]:
            pass_key = ArtifactKey(
                source_hash=ir_key.source_hash,
                phase=f"opt_{pass_cls_name}",
                options_hash="",
            )
            cached = self._cache.get(pass_key)
            if cached:
                module = deserialize_ir(cached)
                out.cache_hits[f"opt_{pass_cls_name}"] = pass_key.source_hash
            else:
                p = pass_cls()
                p.run(module)
                self._cache.set(pass_key, serialize_ir(module))

        if phase == "optimize":
            return out

        emit_key = ArtifactKey(
            source_hash=ir_key.source_hash,
            phase="emit_kotlin",
            options_hash=hashlib.sha256(
                json.dumps(inp.options, sort_keys=True).encode()
            ).hexdigest(),
        )
        emit_cached = self._cache.get(emit_key)
        if emit_cached:
            out.kotlin = emit_cached.decode()
            out.cache_hits["emit_kotlin"] = emit_key.source_hash
        else:
            emitter = KotlinEmitter()
            out.kotlin = emitter.emit(module)
            self._cache.set(emit_key, out.kotlin.encode())

        return out
