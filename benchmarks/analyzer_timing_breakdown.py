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

    timings = {}

    original_create = registry.create_analyzers

    def timed_create():
        analyzers = original_create()

        for analyzer in analyzers:
            original_analyze = analyzer.analyze
            analyzer_id = analyzer.metadata.analyzer_id

            def timed_analyze(
                context,
                _original=original_analyze,
                _id=analyzer_id,
            ):
                started = time.perf_counter()

                try:
                    return _original(context)
                finally:
                    timings[_id] = (
                        time.perf_counter() - started
                    ) * 1000

            analyzer.analyze = timed_analyze

        return analyzers

    registry.create_analyzers = timed_create

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repository = RepositoryLoader().load(str(root))

    started = time.perf_counter()
    run = orchestrator.analyze(repository)
    total = (time.perf_counter() - started) * 1000

    return {
        "total_ms": total,
        "analyzers_recomputed": list(
            run.recomputed_analyzers
        ),
        "analyzers_reused": list(
            run.reused_analyzers
        ),
        "analyzer_times_ms": dict(
            sorted(
                timings.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ),
    }


def main():
    with tempfile.TemporaryDirectory(
        prefix="intellireview-analyzer-timing-"
    ) as tmp:
        root = Path(tmp) / "repo"
        copy_repo(root)

        cache = RepositoryAnalysisCache(str(root))

        # Cold.
        shutil.rmtree(
            root / ".intellireview-cache",
            ignore_errors=True,
        )

        cache = RepositoryAnalysisCache(str(root))
        cold = run_once(root, cache)

        # Warm.
        warm = run_once(root, cache)

        # Incremental change.
        target = root / "analyzer" / "ai" / "acceptance.py"

        original = target.read_text(
            encoding="utf-8"
        )

        target.write_text(
            original
            + "\n# timing benchmark mutation\n",
            encoding="utf-8",
        )

        incremental = run_once(root, cache)

        target.write_text(
            original,
            encoding="utf-8",
        )

        print(
            json.dumps(
                {
                    "cold": cold,
                    "warm": warm,
                    "incremental": incremental,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
