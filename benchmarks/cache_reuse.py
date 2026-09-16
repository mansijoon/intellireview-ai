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


def run_once(root: Path, cache: RepositoryAnalysisCache):
    registry = create_default_analyzer_registry()

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repository = RepositoryLoader().load(str(root))

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
    elapsed = (time.perf_counter() - started) * 1000

    return {
        "wall_time_ms": elapsed,
        "repository_files": len(repository.files),
        "file_cache_gets": stats["gets"],
        "file_cache_hits": stats["hits"],
        "file_cache_misses": stats["misses"],
        "file_cache_reuse_pct": (
            stats["hits"] / stats["gets"] * 100
            if stats["gets"]
            else 0.0
        ),
        "analyzers_recomputed": len(
            run.recomputed_analyzers
        ),
        "analyzers_reused": len(
            run.reused_analyzers
        ),
        "scope_file_count": len(
            repository.analysis_scope or ()
        ),
    }


def main():
    with tempfile.TemporaryDirectory(
        prefix="intellireview-cache-benchmark-"
    ) as tmp:
        root = Path(tmp) / "repo"
        copy_repo(root)

        shutil.rmtree(
            root / ".intellireview-cache",
            ignore_errors=True,
        )

        cache = RepositoryAnalysisCache(str(root))

        # 1. Cold.
        cold = run_once(root, cache)

        # 2. Warm unchanged.
        warm = run_once(root, cache)

        # 3. Single-file change.
        target = root / "analyzer" / "ai" / "acceptance.py"

        original = target.read_text(
            encoding="utf-8"
        )

        target.write_text(
            original
            + "\n# cache reuse benchmark mutation\n",
            encoding="utf-8",
        )

        single = run_once(root, cache)

        target.write_text(
            original,
            encoding="utf-8"
        )

        # 4. Second unchanged run after restoring.
        restored = run_once(root, cache)

        print(
            json.dumps(
                {
                    "benchmark": {
                        "repository": (
                            "actual IntelliReview AI repository"
                        ),
                        "changed_file": (
                            "analyzer/ai/acceptance.py"
                        ),
                    },
                    "cold": cold,
                    "warm": warm,
                    "single_file_incremental": single,
                    "restored_warm": restored,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
