from types import SimpleNamespace

import analyzer.repository_reviewer as repository_reviewer
from analyzer.core.analyzer_defaults import (
    create_default_analyzer_registry,
)
from analyzer.core.analyzers import (
    RepositoryAnalyzerMetadata,
)
from analyzer.core.cache.invalidation import (
    AnalyzerInvalidator,
)
from analyzer.core.models import (
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)


def test_review_repository_wires_selected_rag_context_into_review(
    monkeypatch,
    tmp_path,
):
    source = tmp_path / "auth.py"
    source.write_text(
        "def authenticate(user):\n"
        "    return validate(user)\n",
        encoding="utf-8",
    )

    knowledge = object()

    captured = {}

    monkeypatch.setattr(
        repository_reviewer.RepositoryLoader,
        "load",
        lambda self, path: object(),
    )

    monkeypatch.setattr(
        repository_reviewer,
        "build_repository_knowledge",
        lambda repository: knowledge,
    )

    def fake_select(knowledge_arg, query):
        captured["knowledge"] = knowledge_arg
        captured["query"] = query
        return "selection"

    monkeypatch.setattr(
        repository_reviewer,
        "select_repository_context",
        fake_select,
    )

    monkeypatch.setattr(
        repository_reviewer,
        "format_repository_context",
        lambda selection: (
            "FILE: auth.py\n"
            "CODE:\n"
            "def authenticate(user):\n"
            "    return validate(user)\n"
        ),
    )

    def fake_review(code, repository_context=""):
        captured["code"] = code
        captured["repository_context"] = repository_context
        return {"findings": []}

    monkeypatch.setattr(
        repository_reviewer,
        "review_code",
        fake_review,
    )

    results = repository_reviewer.review_repository(
        str(tmp_path),
        ["auth.py"],
    )

    assert len(results) == 1
    assert results[0]["file"] == "auth.py"
    assert captured["knowledge"] is knowledge
    assert "auth.py" in captured["query"]
    assert "authenticate(user)" in captured["repository_context"]
    assert "validate(user)" in captured["repository_context"]
    assert "authenticate(user)" in captured["code"]


def test_default_analyzer_dependency_metadata_is_consistent():
    registry = create_default_analyzer_registry()
    analyzers = registry.all()

    expected_dependencies = {
        "dependency": set(),
        "architecture": {"dependency"},
        "symbol": {"dependency"},
        "call": {"dependency", "symbol"},
        "architecture_validation": {
            "dependency",
            "architecture",
        },
        "change_impact": {
            "dependency",
            "symbol",
            "call",
        },
        "repository_risk": {
            "dependency",
            "symbol",
            "call",
            "architecture",
            "change_impact",
        },
        "static": set(),
        "complexity": set(),
        "maintainability": {
            "static",
            "complexity",
        },
        "duplication": {"static"},
        "dead_code": {"symbol", "call"},
        "performance": set(),
        "reliability": set(),
        "security": {"static"},
        "taint": {
            "dependency",
            "symbol",
            "call",
        },
        "sbom": {"dependency"},
        "knowledge": {
            "dependency",
            "symbol",
            "call",
        },
    }

    assert set(analyzers) == set(expected_dependencies)

    for analyzer_id, dependencies in expected_dependencies.items():
        metadata = analyzers[analyzer_id].analyzer_class.metadata

        assert metadata.analyzer_id == analyzer_id
        assert metadata.depends_on == frozenset(dependencies)

        for dependency in metadata.depends_on:
            assert dependency in analyzers


def test_analyzer_invalidator_propagates_metadata_dependency_closure():
    class Root:
        metadata = RepositoryAnalyzerMetadata(
            analyzer_id="root",
            name="Root",
            description="Root analyzer",
            source_sensitive=True,
        )

    class Derived:
        metadata = RepositoryAnalyzerMetadata(
            analyzer_id="derived",
            name="Derived",
            description="Derived analyzer",
            depends_on=frozenset({"root"}),
            source_sensitive=False,
        )

    class Final:
        metadata = RepositoryAnalyzerMetadata(
            analyzer_id="final",
            name="Final",
            description="Final analyzer",
            depends_on=frozenset({"derived"}),
            source_sensitive=False,
        )

    class Registry:
        def create_analyzers(self):
            return [Root(), Derived(), Final()]

    class ChangeSet:
        is_empty = False

    invalidated = AnalyzerInvalidator(
        Registry()
    ).invalidated_analyzers(
        ChangeSet(),
        changed_modules={"root"},
    )

    assert invalidated == frozenset({
        "root",
        "derived",
        "final",
    })
