from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceFile:
    """Immutable representation of a repository source file."""

    path: str
    content_hash: str
    size_bytes: int
    line_count: int
    language: str

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("path must not be empty")

        if not self.content_hash:
            raise ValueError("content_hash must not be empty")

        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")

        if self.line_count < 0:
            raise ValueError("line_count must be >= 0")

        if not self.language:
            raise ValueError("language must not be empty")
