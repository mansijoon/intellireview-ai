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


SOURCE_FILES = {
    "app.py": """
from service import process

def main():
    return process(10)
""",
    "service.py": """
from utils import calculate

def process(value):
    return calculate(value) + 1
""",
    "utils.py": """
def calculate(value):
    return value * 2
""",
    "unrelated.py": """
def unrelated():
    return 42
""",
}


def write_repo(root: Path) -> None:
    for name, content in SOURCE_FILES.items():
        path = root / name
        path.write_text(content.strip() + "\n", encoding="utf-8")


def load(root: Path):
    return RepositoryLoader().load(str(root))


def run_once(root: Path, cache: RepositoryAnalysisCache):
    registry = create_default_analyzer_registry()

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repository = load(root)

    cache_stats = {
        "file_cache_hits": 0,
        "file_cache_misses": 0,
        "file_cache_gets": 0,
    }

    original_get = cache.get_file_result

    def instrumented_get(
        analyzer_id,
        path,
        content_hash,
        *,
        variant="",
    ):
        cache_stats["file_cache_gets"] += 1

        result = original_get(
            analyzer_id,
            path,
            content_hash,
            variant=variant,
        )

        if result is None:
            cache_stats["file_cache_misses"] += 1
        else:
            cache_stats["file_cache_hits"] += 1

        return result

    cache.get_file_result = instrumented_get

    started = time.perf_counter()
    run = orchestrator.analyze(repository)
    elapsed = time.perf_counter() - started

    scope = repository.analysis_scope

    return {
        "wall_time_ms": elapsed * 1000,
        "repository_files": len(repository.files),
        "analyzers_returned": len(run.results),
        "analyzers_recomputed": len(run.recomputed_analyzers),
        "analyzers_reused": len(run.reused_analyzers),
        "recomputed_ids": list(run.recomputed_analyzers),
        "reused_ids": list(run.reused_analyzers),
        "scope_files": sorted(scope or ()),
        "file_cache_gets": cache_stats["file_cache_gets"],
        "file_cache_hits": cache_stats["file_cache_hits"],
        "file_cache_misses": cache_stats["file_cache_misses"],
    }


def fresh_cache(root: Path):
    cache_root = root / ".intellireview-cache"

    if cache_root.exists():
        shutil.rmtree(cache_root)

    return RepositoryAnalysisCache(str(root))


def main():
    with tempfile.TemporaryDirectory(
        prefix="intellireview-benchmark-"
    ) as tmp:
        root = Path(tmp)
        write_repo(root)

        # 1. Cold full analysis.
        cache = fresh_cache(root)
        cold = run_once(root, cache)

        # 2. Warm unchanged analysis.
        warm = run_once(root, cache)

        # 3. Single-file modification.
        (root / "utils.py").write_text(
            "def calculate(value):\n"
            "    return value * 3\n",
            encoding="utf-8",
        )

        single = run_once(root, cache)

        # 4. Multi-file modification.
        (root / "service.py").write_text(
            "from utils import calculate\n\n"
            "def process(value):\n"
            "    return calculate(value) + 2\n",
            encoding="utf-8",
        )

        (root / "unrelated.py").write_text(
            "def unrelated():\n"
            "    return 99\n",
            encoding="utf-8",
        )

        multi = run_once(root, cache)

        cold_file_work = cold["file_cache_misses"]

        def file_reduction(run):
            if cold_file_work == 0:
                return 0.0

            return (
                1
                - run["file_cache_misses"] / cold_file_work
            ) * 100

        def file_cache_reuse(run):
            gets = run["file_cache_gets"]

            if gets == 0:
                return 0.0

            return (
                run["file_cache_hits"] / gets
            ) * 100

        def speedup(run):
            if run["wall_time_ms"] == 0:
                return 0.0

            return (
                cold["wall_time_ms"]
                / run["wall_time_ms"]
            )

        report = {
            "cold_full": cold,
            "warm_full": warm,
            "single_file_change": single,
            "multi_file_change": multi,
            "derived_metrics": {
                "single_file_file_work_reduction_pct":
                    file_reduction(single),
                "multi_file_file_work_reduction_pct":
                    file_reduction(multi),
                "warm_file_cache_reuse_pct":
                    file_cache_reuse(warm),
                "single_file_cache_reuse_pct":
                    file_cache_reuse(single),
                "multi_file_cache_reuse_pct":
                    file_cache_reuse(multi),
                "single_file_speedup_vs_cold":
                    speedup(single),
                "multi_file_speedup_vs_cold":
                    speedup(multi),
            },
        }

        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
