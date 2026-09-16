from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path

from analyzer.core.analyzer_defaults import create_default_analyzer_registry
from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.repository_loader import RepositoryLoader
from analyzer.core.repository_orchestrator import RepositoryAnalysisOrchestrator


FILE_COUNT = 100


def write_repo(root: Path) -> None:
    for i in range(FILE_COUNT):
        if i == 0:
            content = """
def value():
    return 1
"""
        else:
            content = f"""
from module_{i - 1:03d} import value

def value_{i}():
    return value() + {i}
"""
        (root / f"module_{i:03d}.py").write_text(
            content.strip() + "\n",
            encoding="utf-8",
        )

    for i in range(10):
        (root / f"isolated_{i:03d}.py").write_text(
            f"""
def isolated_{i}():
    return {i}
""".strip() + "\n",
            encoding="utf-8",
        )


def load(root: Path):
    return RepositoryLoader().load(str(root))


def run_once(root: Path, cache: RepositoryAnalysisCache):
    registry = create_default_analyzer_registry()

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repository = load(root)

    stats = {
        "gets": 0,
        "hits": 0,
        "misses": 0,
    }

    original_get = cache.get_file_result

    def instrumented_get(
        analyzer_id,
        path,
        content_hash,
        *,
        variant="",
    ):
        stats["gets"] += 1

        result = original_get(
            analyzer_id,
            path,
            content_hash,
            variant=variant,
        )

        if result is None:
            stats["misses"] += 1
        else:
            stats["hits"] += 1

        return result

    cache.get_file_result = instrumented_get

    started = time.perf_counter()
    run = orchestrator.analyze(repository)
    elapsed = time.perf_counter() - started

    return {
        "wall_time_ms": elapsed * 1000,
        "repository_files": len(repository.files),
        "analyzers_returned": len(run.results),
        "analyzers_recomputed": len(run.recomputed_analyzers),
        "analyzers_reused": len(run.reused_analyzers),
        "file_cache_gets": stats["gets"],
        "file_cache_hits": stats["hits"],
        "file_cache_misses": stats["misses"],
        "scope_files": sorted(repository.analysis_scope or ()),
    }


def fresh_cache(root: Path):
    cache_root = root / ".intellireview-cache"

    if cache_root.exists():
        shutil.rmtree(cache_root)

    return RepositoryAnalysisCache(str(root))


def median(values):
    values = sorted(values)
    n = len(values)

    if n % 2:
        return values[n // 2]

    return (values[n // 2 - 1] + values[n // 2]) / 2


def main():
    with tempfile.TemporaryDirectory(
        prefix="intellireview-large-benchmark-"
    ) as tmp:
        root = Path(tmp)
        write_repo(root)

        cache = fresh_cache(root)

        # Cold run.
        cold = run_once(root, cache)

        # Warm unchanged run.
        warm = run_once(root, cache)

        # Single-file change at the beginning of the dependency chain.
        (root / "module_000.py").write_text(
            """
def value():
    return 2
""".strip() + "\n",
            encoding="utf-8",
        )

        single_runs = [
            run_once(root, cache)
            for _ in range(5)
        ]

        # Multi-file change: one dependency-chain file plus one isolated file.
        (root / "module_050.py").write_text(
            """
from module_049 import value

def value_50():
    return value() + 5000
""".strip() + "\n",
            encoding="utf-8",
        )

        (root / "isolated_000.py").write_text(
            """
def isolated_0():
    return 9999
""".strip() + "\n",
            encoding="utf-8",
        )

        multi_runs = [
            run_once(root, cache)
            for _ in range(5)
        ]

        cold_work = cold["file_cache_misses"]

        def reduction(run):
            if cold_work == 0:
                return 0.0
            return (1 - run["file_cache_misses"] / cold_work) * 100

        def reuse(run):
            if run["file_cache_gets"] == 0:
                return 0.0
            return run["file_cache_hits"] / run["file_cache_gets"] * 100

        def speedup(run):
            if run["wall_time_ms"] == 0:
                return 0.0
            return cold["wall_time_ms"] / run["wall_time_ms"]

        single_median = median(
            [x["wall_time_ms"] for x in single_runs]
        )

        multi_median = median(
            [x["wall_time_ms"] for x in multi_runs]
        )

        single_reference = dict(single_runs[0])
        multi_reference = dict(multi_runs[0])

        single_reference["wall_time_ms_median"] = single_median
        multi_reference["wall_time_ms_median"] = multi_median

        single_speedup = (
            cold["wall_time_ms"] / single_median
            if single_median
            else 0.0
        )

        multi_speedup = (
            cold["wall_time_ms"] / multi_median
            if multi_median
            else 0.0
        )

        report = {
            "benchmark": {
                "repository_files": FILE_COUNT + 10,
                "dependency_chain_files": FILE_COUNT,
                "isolated_files": 10,
                "single_change": "module_000.py",
                "multi_change": [
                    "module_050.py",
                    "isolated_000.py",
                ],
                "timed_repetitions": 5,
            },
            "cold_full": cold,
            "warm_full": warm,
            "single_file_change": single_reference,
            "multi_file_change": multi_reference,
            "derived_metrics": {
                "single_file_granular_work_reduction_pct":
                    reduction(single_reference),
                "multi_file_granular_work_reduction_pct":
                    reduction(multi_reference),
                "single_file_cache_reuse_pct":
                    reuse(single_reference),
                "multi_file_cache_reuse_pct":
                    reuse(multi_reference),
                "single_file_median_speedup_vs_cold":
                    single_speedup,
                "multi_file_median_speedup_vs_cold":
                    multi_speedup,
            },
        }

        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
