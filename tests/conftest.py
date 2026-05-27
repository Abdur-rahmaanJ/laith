from __future__ import annotations
import pytest
import time
import sys


@pytest.fixture(scope="session")
def parser():
    from laith.compiler.frontend.analyzer import Parser
    return Parser


@pytest.fixture(scope="session")
def analyzer_factory():
    from laith.compiler.frontend.analyzer import SemanticAnalyzer
    return lambda: SemanticAnalyzer()


@pytest.fixture(scope="session")
def emitter_factory():
    from laith.compiler.backend.kotlin.emitter import KotlinEmitter
    return lambda: KotlinEmitter()


@pytest.fixture(scope="session")
def cpp_emitter_factory():
    from laith.compiler.backend.native.emitter import CPPEmitter
    return lambda: CPPEmitter()


@pytest.fixture(scope="session")
def ir_pool():
    from tests.helpers.pool import IRPool
    return IRPool()


@pytest.fixture(scope="session")
def ir_arena():
    from tests.helpers.pool import IRArena
    return IRArena()


@pytest.fixture(scope="session")
def compile_pipeline():
    from tests.helpers.compiler_fixtures import CompilePipeline
    return CompilePipeline()


@pytest.fixture(scope="session")
def cache_dir(tmp_path_factory) -> str:
    return str(tmp_path_factory.mktemp("laith-cache"))


@pytest.fixture(scope="session")
def golden_dir(tmp_path_factory) -> str:
    return str(tmp_path_factory.mktemp("laith-golden"))


@pytest.fixture
def fresh_analyzer(analyzer_factory):
    return analyzer_factory()


@pytest.fixture
def fresh_emitter(emitter_factory):
    return emitter_factory()


@pytest.fixture
def fresh_cpp_emitter(cpp_emitter_factory):
    return cpp_emitter_factory()


# Startup tracing
@pytest.hookimpl(hookwrapper=True)
def pytest_load_initial_conftests(early_config, parser, args):
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    if elapsed > 0.5:
        print(f"\n[perf] conftest loading: {elapsed:.3f}s")


# Collection time tracking
@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    if elapsed > 0.5:
        print(f"[perf] Collection: {elapsed:.3f}s for {len(session.items)} tests")


# Test duration logging
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    if elapsed > 1.0:
        print(f"[perf] Slow test: {item.nodeid} ({elapsed:.3f}s)")
