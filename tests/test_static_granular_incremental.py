import hashlib
from pathlib import Path
from unittest.mock import patch

from analyzer.core.cache import RepositoryAnalysisCache
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext
from analyzer.static.repository_analyzer import StaticRepositoryAnalyzer


def make_repository(root: Path, revision: str):
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
        repository_id="static-granular-test",
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


def test_static_cache_is_content_addressed_per_file(tmp_path):
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
    analyzer = StaticRepositoryAnalyzer()

    repo1 = make_repository(tmp_path, "r1")
    repo1.configuration[
        "_intellireview_analysis_cache"
    ] = cache

    result1 = analyzer.analyze(repo1)

    assert result1.status.value == "success"

    # All three files must now have cached rule results.
    rules = [
        rule
        for rule in __import__(
            "analyzer.static.repository_analyzer",
            fromlist=["create_default_registry"],
        ).create_default_registry().create_rules()
        if rule.metadata.category != "security"
    ]

    for name in ("a.py", "b.py", "c.py"):
        source = next(
            source_file
            for source_file in repo1.files
            if source_file.path == name
        )

        for rule in rules:
            cached = cache.get_file_result(
                "static",
                name,
                source.content_hash,
                variant=rule.metadata.rule_id,
            )

            assert isinstance(cached, tuple)

    # Change only b.py.
    (tmp_path / "b.py").write_text(
        "def b():\n"
        "    return 999\n"
    )

    repo2 = make_repository(tmp_path, "r2")
    repo2.configuration[
        "_intellireview_analysis_cache"
    ] = cache

    # Capture cache misses. A miss corresponds to work that
    # must be recomputed by the static analyzer.
    original_get = cache.get_file_result
    misses = []

    def tracked_get(
        analyzer_id,
        path,
        content_hash,
        *,
        variant="",
    ):
        value = original_get(
            analyzer_id,
            path,
            content_hash,
            variant=variant,
        )

        if value is None:
            misses.append((path, variant))

        return value

    with patch.object(
        cache,
        "get_file_result",
        side_effect=tracked_get,
    ):
        result2 = analyzer.analyze(repo2)

    assert result2.status.value == "success"

    # Every cache miss must belong to the changed file.
    assert misses
    assert {
        path
        for path, _ in misses
    } == {"b.py"}

    # There must be no misses for unchanged files.
    assert not any(
        path in {"a.py", "c.py"}
        for path, _ in misses
    )
