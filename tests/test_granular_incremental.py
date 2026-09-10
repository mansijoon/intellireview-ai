from pathlib import Path
from unittest.mock import patch

from analyzer.complexity.repository_analyzer import ComplexityRepositoryAnalyzer
from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.repository_context import RepositoryContext


def make_repository(root: Path, revision: str) -> RepositoryContext:
    files = []

    for name in ("a.py", "b.py", "c.py"):
        path = root / name
        content = path.read_text()

        from analyzer.core.models import SourceFile
        import hashlib

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
        repository_id="granular-test",
        revision=revision,
        root_path=str(root),
        files=tuple(files),
        source_contents={
            source_file.path: (
                root / source_file.path
            ).read_text()
            for source_file in files
        },
        configuration={},
    )


def test_complexity_reuses_unchanged_files(tmp_path):
    (tmp_path / "a.py").write_text(
        "def a():\n    return 1\n"
    )
    (tmp_path / "b.py").write_text(
        "def b():\n    return 2\n"
    )
    (tmp_path / "c.py").write_text(
        "def c():\n    return 3\n"
    )

    cache = RepositoryAnalysisCache(str(tmp_path))

    repo1 = make_repository(tmp_path, "r1")
    repo1.configuration["_intellireview_analysis_cache"] = cache

    analyzer = ComplexityRepositoryAnalyzer()

    with patch(
        "analyzer.complexity.repository_analyzer.calculate_metrics",
        wraps=__import__(
            "analyzer.complexity.repository_analyzer",
            fromlist=["calculate_metrics"],
        ).calculate_metrics,
    ) as calculate:
        analyzer.analyze(repo1)

        assert calculate.call_count == 3

    (tmp_path / "b.py").write_text(
        "def b():\n    return 999\n"
    )

    repo2 = make_repository(tmp_path, "r2")
    repo2.configuration["_intellireview_analysis_cache"] = cache

    with patch(
        "analyzer.complexity.repository_analyzer.calculate_metrics",
        wraps=__import__(
            "analyzer.complexity.repository_analyzer",
            fromlist=["calculate_metrics"],
        ).calculate_metrics,
    ) as calculate:
        analyzer.analyze(repo2)

        assert calculate.call_count == 1

        called_path = calculate.call_args.args[0]

        assert "999" in called_path
