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


SOURCE = Path.cwd()


def copy_source_repo(destination: Path) -> None:
    shutil.copytree(
        SOURCE,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            "venv",
            ".intellireview-cache",
            "__pycache__",
            ".pytest_cache",
            "build",
            "dist",
            "*.egg-info",
            "uploads",
            "reports",
        ),
        dirs_exist_ok=True,
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
        "scope_file_count": len(repository.analysis_scope or ()),
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
        prefix="intellireview-real-benchmark-"
    ) as tmp:
        root = Path(tmp) / "repo"
        copy_source_repo(root)

        cache = fresh_cache(root)

        # Cold baseline.
        cold = run_once(root, cache)

        # Warm unchanged.
        warm = run_once(root, cache)

        python_files = sorted(root.rglob("*.py"))

        if not python_files:
            raise SystemExit("No Python files found")

        # Change one real project source file.
        target = next(
            (
                p for p in python_files
                if "benchmarks" not in p.parts
                and p.name != "__init__.py"
            ),
            python_files[0],
        )

        original = target.read_text(encoding="utf-8")

        target.write_text(
            original + "\n# incremental benchmark mutation\n",
            encoding="utf-8",
        )

        single = run_once(root, cache)

        # Restore source before exiting.
        target.write_text(original, encoding="utf-8")

        cold_work = cold["file_cache_misses"]

        report = {
            "benchmark": {
                "repository": "actual IntelliReview AI repository",
                "timed_repetitions": 1,
                "single_file_change": str(
                    target.relative_to(root)
                ),
            },
            "cold_full": cold,
            "warm_full": warm,
            "single_file_change": single,
            "derived_metrics": {
                "single_file_granular_work_reduction_pct": (
                    (1 - single["file_cache_misses"] / cold_work) * 100
                    if cold_work else 0.0
                ),
                "single_file_cache_reuse_pct": (
                    single["file_cache_hits"]
                    / single["file_cache_gets"]
                    * 100
                    if single["file_cache_gets"] else 0.0
                ),
                "single_file_speedup_vs_cold": (
                    cold["wall_time_ms"]
                    / single["wall_time_ms"]
                    if single["wall_time_ms"] else 0.0
                ),
            },
        }

        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
