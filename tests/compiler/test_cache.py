from __future__ import annotations
import pytest
from laith.compiler.cache import CacheStore, ArtifactKey
from laith.compiler.pipeline import IncrementalCompiler, BuildInput, SourceFile
from laith.compiler.hash import structural_hash
from laith.compiler.ir.nodes import IRModule, IRFunction, IRBlock
from laith.compiler.frontend.symbols import INT_TYPE


class TestCache:
    def test_artifact_key_from_source(self):
        key1 = ArtifactKey.from_source("def f(): pass", "parse")
        key2 = ArtifactKey.from_source("def f(): pass", "parse")
        assert key1.source_hash == key2.source_hash

    def test_artifact_key_different_sources(self):
        key1 = ArtifactKey.from_source("def f(): pass", "parse")
        key2 = ArtifactKey.from_source("def g(): pass", "parse")
        assert key1.source_hash != key2.source_hash

    def test_artifact_key_different_phases(self):
        key1 = ArtifactKey.from_source("def f(): pass", "parse")
        key2 = ArtifactKey.from_source("def f(): pass", "emit")
        assert key1.options_hash == key2.options_hash

    def test_cache_store_set_get(self, tmp_path):
        cache = CacheStore(tmp_path)
        key = ArtifactKey(source_hash="abc123", phase="test", options_hash="def456")
        cache.set(key, b"hello world")
        result = cache.get(key)
        assert result == b"hello world"

    def test_cache_store_miss(self, tmp_path):
        cache = CacheStore(tmp_path)
        key = ArtifactKey(source_hash="nonexistent", phase="test", options_hash="missing")
        result = cache.get(key)
        assert result is None

    def test_cache_store_invalidate(self, tmp_path):
        cache = CacheStore(tmp_path)
        key = ArtifactKey(source_hash="abc123", phase="test", options_hash="def456")
        cache.set(key, b"hello")
        cache.invalidate("abc123")
        result = cache.get(key)
        assert result is None

    def test_cache_get_or_compute(self, tmp_path):
        cache = CacheStore(tmp_path)
        key = ArtifactKey(source_hash="abc123", phase="test", options_hash="def456")
        computed = []

        def compute():
            computed.append(1)
            return b"computed"

        result1 = cache.get_or_compute(key, compute)
        assert result1 == b"computed"
        assert len(computed) == 1

        result2 = cache.get_or_compute(key, compute)
        assert result2 == b"computed"
        assert len(computed) == 1  # compute not called again

    def test_cache_stats(self, tmp_path):
        cache = CacheStore(tmp_path)
        assert cache.stats()["files"] == 0
        key = ArtifactKey(source_hash="abc", phase="test", options_hash="def")
        cache.set(key, b"data")
        stats = cache.stats()
        assert stats["files"] >= 1
        assert stats["size_bytes"] >= 4


class TestIncrementalCompiler:
    def test_build_input_creation(self):
        src = SourceFile(path="test.py", content="def f(): return 1")
        inp = BuildInput(sources={"test": src})
        assert "test" in inp.sources
        assert inp.sources["test"].fingerprint != ""

    def test_source_file_fingerprint(self):
        src1 = SourceFile(path="a.py", content="def f(): return 1")
        src2 = SourceFile(path="b.py", content="def f(): return 1")
        assert src1.fingerprint == src2.fingerprint

    def test_source_file_different_content(self):
        src1 = SourceFile(path="a.py", content="def f(): return 1")
        src2 = SourceFile(path="b.py", content="def f(): return 2")
        assert src1.fingerprint != src2.fingerprint


class TestStructuralHash:
    def test_same_ir_same_hash(self):
        b1 = IRBlock(label="entry")
        b2 = IRBlock(label="entry")
        f1 = IRFunction(name="f", return_type=INT_TYPE, args=[], blocks=[b1])
        f2 = IRFunction(name="f", return_type=INT_TYPE, args=[], blocks=[b2])
        m1 = IRModule(functions=[f1])
        m2 = IRModule(functions=[f2])
        assert structural_hash(m1) == structural_hash(m2)

    def test_different_names_different_hash(self):
        f1 = IRFunction(name="f", return_type=INT_TYPE, args=[])
        f2 = IRFunction(name="g", return_type=INT_TYPE, args=[])
        m1 = IRModule(functions=[f1])
        m2 = IRModule(functions=[f2])
        assert structural_hash(m1) != structural_hash(m2)
