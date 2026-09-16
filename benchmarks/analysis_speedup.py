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
REPETITIONS = 7


def copy_repo(destination: Path) -> None:
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


def run_analysis(root: Path, cache: RepositoryAnalysisCache) -> float:
    registry = create_default_analyzer_registry()

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repository = RepositoryLoader().load(str(root))

    started = time.perf_counter()
    orchestrator.analyze(repository)
    return (time.perf_counter() - started) * 1000


def median(values):
    values = sorted(values)
    n = len(values)

    if n % 2:
        return values[n // 2]

    return (values[n // 2 - 1] + values[n // 2]) / 2


def main():
    with tempfile.TemporaryDirectory(
        prefix="intellireview-speedup-"
    ) as tmp:
        root = Path(tmp) / "repo"
        copy_repo(root)

        cache = RepositoryAnalysisCache(
            str(root)
        )

        # ---------------------------------------------------------
        # 1. Cold baseline.
        # ---------------------------------------------------------
        shutil.rmtree(
            root / ".intellireview-cache",
            ignore_errors=True,
        )

        cache = RepositoryAnalysisCache(str(root))

        cold_samples = [
            run_analysis(root, cache)
            for _ in range(REPETITIONS)
        ]

        # ---------------------------------------------------------
        # 2. Warm unchanged analysis.
        # ---------------------------------------------------------
        warm_samples = [
            run_analysis(root, cache)
            for _ in range(REPETITIONS)
        ]

        # ---------------------------------------------------------
        # 3. Single-file incremental analysis.
        # ---------------------------------------------------------
        python_files = sorted(root.rglob("*.py"))

        target = next(
            (
                p for p in python_files
                if "benchmarks" not in p.parts
                and p.name != "__init__.py"
            ),
            python_files[0],
        )

        original = target.read_text(
            encoding="utf-8"
        )

        target.write_text(
            original
            + "\n# speedup benchmark mutation\n",
            encoding="utf-8",
        )

        incremental_samples = [
            run_analysis(root, cache)
            for _ in range(REPETITIONS)
        ]

        target.write_text(
            original,
            encoding="utf-8",
        )

        cold_median = median(cold_samples)
        warm_median = median(warm_samples)
        incremental_median = median(
            incremental_samples
        )

        report = {
            "benchmark": {
                "repository": "actual IntelliReview AI repository",
                "repository_files": len(
                    python_files
                ),
                "repetitions_per_condition": REPETITIONS,
                "incremental_change": str(
                    target.relative_to(root)
                ),
            },
            "cold_full": {
                "samples_ms": cold_samples,
                "median_ms": cold_median,
            },
            "warm_full": {
                "samples_ms": warm_samples,
                "median_ms": warm_median,
            },
            "incremental_single_file": {
                "samples_ms": incremental_samples,
                "median_ms": incremental_median,
            },
            "derived_metrics": {
                "warm_speedup_vs_cold": (
                    cold_median / warm_median
                    if warm_median
                    else 0.0
                ),
                "incremental_speedup_vs_cold": (
                    cold_median / incremental_median
                    if incremental_median
                    else 0.0
                ),
                "warm_runtime_reduction_pct": (
                    (
                        1
                        - warm_median / cold_median
                    )
                    * 100
                    if cold_median
                    else 0.0
                ),
                "incremental_runtime_reduction_pct": (
                    (
                        1
                        - incremental_median
                        / cold_median
                    )
                    * 100
                    if cold_median
                    else 0.0
                ),
            },
        }

        print(
            json.dumps(
                report,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
