import hashlib
from pathlib import Path
from unittest.mock import patch

from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext
from analyzer.performance.repository_analyzer import (
    PerformanceRepositoryAnalyzer,
)
from analyzer.reliability.repository_analyzer import (
    ReliabilityRepositoryAnalyzer,
)


def make_repository(
    root: Path,
    revision: str,
    cache: RepositoryAnalysisCache,
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
        repository_id="granular-source-analyzers",
        revision=revision,
        root_path=str(root),
        files=tuple(files),
        source_contents={
            source_file.path: (
                root / source_file.path
            ).read_text()
            for source_file in files
        },
        configuration={
            "_intellireview_analysis_cache": cache,
        },
    )


def test_performance_recomputes_only_changed_file(tmp_path):
    for name in ("a.py", "b.py", "c.py"):
        (tmp_path / name).write_text(
            f"def {name[0]}():\n"
            f"    return 1\n"
        )

    cache = RepositoryAnalysisCache(str(tmp_path))
    analyzer = PerformanceRepositoryAnalyzer()

    repo1 = make_repository(tmp_path, "r1", cache)
    result1 = analyzer.analyze(repo1)

    assert result1.status.value == "success"

    (tmp_path / "b.py").write_text(
        "def b():\n"
        "    for x in items:\n"
        "        for y in items:\n"
        "            pass\n"
    )

    repo2 = make_repository(tmp_path, "r2", cache)
    repo2.configuration[
        "_intellireview_analysis_scope"
    ] = frozenset({"b.py"})

    from analyzer.performance import rules

    original = rules.NestedLoopRule.analyze
    calls = []

    def tracked(self, context):
        calls.append(context.file_path)
        return original(self, context)

    with patch.object(
        rules.NestedLoopRule,
        "analyze",
        tracked,
    ):
        result2 = analyzer.analyze(repo2)

    assert result2.status.value == "success"
    assert calls == ["b.py"]

    report = result2.artifacts["performance_report"]

    assert any(
        item.file_path == "b.py"
        for item in report.files
    )


def test_reliability_recomputes_only_changed_file(tmp_path):
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
    analyzer = ReliabilityRepositoryAnalyzer()

    repo1 = make_repository(tmp_path, "r1", cache)
    result1 = analyzer.analyze(repo1)

    assert result1.status.value == "success"

    (tmp_path / "b.py").write_text(
        "def b():\n"
        "    try:\n"
        "        return 2\n"
        "    except:\n"
        "        pass\n"
    )

    repo2 = make_repository(tmp_path, "r2", cache)
    repo2.configuration[
        "_intellireview_analysis_scope"
    ] = frozenset({"b.py"})

    from analyzer.reliability import rules

    original = rules.BareExceptRule.analyze
    calls = []

    def tracked(self, context):
        calls.append(context.file_path)
        return original(self, context)

    with patch.object(
        rules.BareExceptRule,
        "analyze",
        tracked,
    ):
        result2 = analyzer.analyze(repo2)

    assert result2.status.value == "success"
    assert calls == ["b.py"]

    report = result2.artifacts["reliability_report"]

    assert any(
        item.file_path == "b.py"
        for item in report.files
    )
