from __future__ import annotations

from dataclasses import dataclass, field

from .source_file import SourceFile


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Immutable snapshot of a repository at an analysis point."""

    repository_id: str
    revision: str
    root_path: str
    files: tuple[SourceFile, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.repository_id.strip():
            raise ValueError("repository_id must not be empty")

        if not self.revision.strip():
            raise ValueError("revision must not be empty")

        if not self.root_path.strip():
            raise ValueError("root_path must not be empty")
