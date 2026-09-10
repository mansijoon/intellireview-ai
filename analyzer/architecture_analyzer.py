from __future__ import annotations

from pathlib import Path

from analyzer.architecture_repository_analyzer import (
    ArchitectureRepositoryAnalyzer,
)
from analyzer.core import RepositoryLoader


def analyze_repository_architecture(
    repo_path,
    repo_files,
):
    """
    Compatibility API for the legacy architecture analyzer.
    """

    repository = RepositoryLoader().load(
        repo_path,
        repository_id="legacy-repository",
        revision="working-tree",
    )

    allowed_files = set(repo_files)

    repository.files = tuple(
        source_file
        for source_file in repository.files
        if source_file.path in allowed_files
    )

    result = ArchitectureRepositoryAnalyzer().analyze(
        repository
    )

    return result.artifacts.get(
        "architecture_findings",
        [],
    )
