from __future__ import annotations
import pytest
import time


@pytest.fixture(scope="session")
def benchmark():
    class BenchmarkCollector:
        def __init__(self):
            self._results = {}

        def measure(self, name: str, func: callable, iterations: int = 10, warmup: int = 3):
            for _ in range(warmup):
                func()

            samples = []
            for _ in range(iterations):
                t0 = time.perf_counter_ns()
                func()
                elapsed = time.perf_counter_ns() - t0
                samples.append(elapsed)

            self._results[name] = {
                "samples": samples,
                "mean_ns": sum(samples) / len(samples),
                "min_ns": min(samples),
                "max_ns": max(samples),
                "iterations": iterations,
            }

        def report(self):
            for name, data in sorted(self._results.items()):
                mean_ms = data["mean_ns"] / 1_000_000
                min_ms = data["min_ns"] / 1_000_000
                max_ms = data["max_ns"] / 1_000_000
                print(f"  {name}: {mean_ms:.3f}ms (min={min_ms:.3f}ms max={max_ms:.3f}ms) [{data['iterations']} samples]")

    collector = BenchmarkCollector()
    yield collector
    collector.report()
