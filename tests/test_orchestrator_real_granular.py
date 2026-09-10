import hashlib
from pathlib import Path
from unittest.mock import patch

from analyzer.complexity.repository_analyzer import (
    ComplexityRepositoryAnalyzer,
)
from analyzer.core.analyzer_registry import (
    RepositoryAnalyzerRegistry,
)
from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.repository_orchestrator import (
    RepositoryAnalysisOrchestrator,
)


def make_repository(
    root: Path,
    revision: str,
) -> RepositoryContext:
    files = []

    for name in ("a.py", "b.py", "c.py"):
        content = (root / name).read_text()

        files.append(
            SourceFile(
                path=name,
                content_hash=hashlib.sha256(
                    content.encode()
                ).hexdigest(),
                size_bytes=len(content.encode()),
                line_count=content.count("\n") + 1,
                language="python",
            )
        )

    return RepositoryContext(
        repository_id="real-granular-test",
        revision=revision,
        root_path=str(root),
        files=tuple(files),
        source_contents={
            source_file.path:
                (root / source_file.path).read_text()
            for source_file in files
        },
        configuration={},
    )


def test_orchestrator_runs_real_complexity_only_for_scoped_files(
    tmp_path,
):
    (tmp_path / "a.py").write_text(
        "def a():\n"
        "    return 1\n"
    )
    (tmp_path / "b.py").write_text(
        "def b():\n"
        "    return 2\n"
    )
    (tmp_path / "c.py").write_text(
        "def c():\n"
        "    return 3\n"
    )

    cache = RepositoryAnalysisCache(str(tmp_path))

    registry = RepositoryAnalyzerRegistry()
    registry.register(ComplexityRepositoryAnalyzer)

    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    repo1 = make_repository(
        tmp_path,
        "r1",
    )

    with patch(
        "analyzer.complexity.repository_analyzer.calculate_metrics",
        wraps=__import__(
            "analyzer.complexity.repository_analyzer",
            fromlist=["calculate_metrics"],
        ).calculate_metrics,
    ) as calculate:
        orchestrator.analyze(repo1)

        assert calculate.call_count == 3

    # Change only b.py.
    (tmp_path / "b.py").write_text(
        "def b():\n"
        "    return 999\n"
    )

    repo2 = make_repository(
        tmp_path,
        "r2",
    )

    with patch(
        "analyzer.complexity.repository_analyzer.calculate_metrics",
        wraps=__import__(
            "analyzer.complexity.repository_analyzer",
            fromlist=["calculate_metrics"],
        ).calculate_metrics,
    ) as calculate:
        orchestrator.analyze(repo2)

        assert calculate.call_count == 1

        assert "999" in calculate.call_args.args[0]
