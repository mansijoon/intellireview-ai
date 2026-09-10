from __future__ import annotations

from pathlib import Path

import pytest

from analyzer.core.git_repository import GitRepository


ROOT = Path(__file__).resolve().parent


def test_resolve_head_to_full_sha() -> None:
    repository = GitRepository(str(ROOT))

    resolved = repository.resolve_revision("HEAD")

    assert len(resolved) == 40
    assert resolved == repository.commit("HEAD").hexsha


def test_resolve_parent_revision() -> None:
    repository = GitRepository(str(ROOT))

    head = repository.resolve_revision("HEAD")
    parent = repository.resolve_revision("HEAD~1")

    assert len(head) == 40
    assert len(parent) == 40
    assert head != parent


def test_list_files_reads_exact_committed_tree() -> None:
    repository = GitRepository(str(ROOT))

    files = repository.list_files("HEAD")

    assert files
    assert files == tuple(sorted(files))
    assert "analyzer/core/repository_loader.py" in files


def test_read_file_comes_from_commit_not_working_tree() -> None:
    repository = GitRepository(str(ROOT))

    committed = repository.read_file(
        "HEAD",
        "analyzer/core/repository_loader.py",
    )

    expected = (
        repository.commit("HEAD")
        .tree / "analyzer/core/repository_loader.py"
    ).data_stream.read()

    assert committed == expected


def test_invalid_revision_is_rejected() -> None:
    repository = GitRepository(str(ROOT))

    with pytest.raises(ValueError, match="Invalid Git revision"):
        repository.resolve_revision(
            "definitely-not-a-real-revision"
        )


def test_empty_revision_is_rejected() -> None:
    repository = GitRepository(str(ROOT))

    with pytest.raises(ValueError, match="revision must not be empty"):
        repository.resolve_revision("")


def test_missing_committed_file_is_rejected() -> None:
    repository = GitRepository(str(ROOT))

    with pytest.raises(FileNotFoundError):
        repository.read_file(
            "HEAD",
            "this/file/does/not/exist.py",
        )
