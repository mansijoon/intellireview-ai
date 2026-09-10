import hashlib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.models import (
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
    SourceFile,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.repository_orchestrator import (
    RepositoryAnalysisOrchestrator,
)
from analyzer.dependency.models import (
    DependencyGraph,
    ModuleNode,
)


class FakeDependencyAnalyzer(RepositoryAnalyzer):
    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="dependency",
        name="Fake Dependency",
        description="Test dependency analyzer.",
        source_sensitive=True,
    )

    def analyze(self, repository):
        started = datetime.now(timezone.utc)

        graph = DependencyGraph()

        a = ModuleNode(
            name="a",
            path="a.py",
            imported_by={"b"},
        )

        b = ModuleNode(
            name="b",
            path="b.py",
            imports={"a"},
        )

        c = ModuleNode(
            name="c",
            path="c.py",
        )

        graph.add_module(a)
        graph.add_module(b)
        graph.add_module(c)

        result = RepositoryAnalysisResult(
            analyzer_id="dependency",
            status=RepositoryAnalysisStatus.SUCCESS,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
            artifacts={
                "dependency_graph": graph,
            },
        )

        repository.set_artifact(
            "dependency_analysis",
            result,
        )

        return result


class FakeScopedAnalyzer(RepositoryAnalyzer):
    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="scoped",
        name="Fake Scoped Analyzer",
        description="Test scoped analyzer.",
        source_sensitive=True,
    )

    calls: list[str] = []

    def analyze(self, repository):
        started = datetime.now(timezone.utc)

        scope = repository.analysis_scope

        for source_file in repository.files:
            if (
                scope is not None
                and source_file.path not in scope
            ):
                continue

            self.calls.append(source_file.path)

        result = RepositoryAnalysisResult(
            analyzer_id="scoped",
            status=RepositoryAnalysisStatus.SUCCESS,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
            artifacts={
                "analysis_scope": scope,
            },
        )

        return result


class FakeRegistry:
    def create_analyzers(self):
        return [
            FakeDependencyAnalyzer(),
            FakeScopedAnalyzer(),
        ]


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
        repository_id="orchestrator-incremental-test",
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


def test_orchestrator_builds_dependency_aware_scope(tmp_path):
    for name, value in (
        ("a.py", "1"),
        ("b.py", "2"),
        ("c.py", "3"),
    ):
        (tmp_path / name).write_text(
            f"def {name[0]}():\n"
            f"    return {value}\n"
        )

    cache = RepositoryAnalysisCache(str(tmp_path))

    registry = FakeRegistry()
    orchestrator = RepositoryAnalysisOrchestrator(
        registry,
        cache=cache,
    )

    FakeScopedAnalyzer.calls = []

    repo1 = make_repository(
        tmp_path,
        "r1",
    )

    first = orchestrator.analyze(repo1)

    assert first.status == RepositoryAnalysisStatus.SUCCESS
    assert set(FakeScopedAnalyzer.calls) == {
        "a.py",
        "b.py",
        "c.py",
    }

    # Change only a.py. Because b.py imports a.py,
    # both a.py and b.py must be in the incremental scope.
    (tmp_path / "a.py").write_text(
        "def a():\n"
        "    return 999\n"
    )

    FakeScopedAnalyzer.calls = []

    repo2 = make_repository(
        tmp_path,
        "r2",
    )

    second = orchestrator.analyze(repo2)

    assert second.status == RepositoryAnalysisStatus.SUCCESS

    assert set(FakeScopedAnalyzer.calls) == {
        "a.py",
        "b.py",
    }

    assert "c.py" not in FakeScopedAnalyzer.calls

    scoped_result = next(
        result
        for result in second.results
        if result.analyzer_id == "scoped"
    )

    assert scoped_result.artifacts[
        "analysis_scope"
    ] == frozenset({
        "a.py",
        "b.py",
    })
