from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """A precise location within a source file."""

    file_path: str
    line_start: int
    line_end: int | None = None
    column_start: int | None = None
    column_end: int | None = None

    def __post_init__(self) -> None:
        if not self.file_path:
            raise ValueError("file_path must not be empty")

        if self.line_start < 1:
            raise ValueError("line_start must be >= 1")

        if self.line_end is not None and self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")

        if self.column_start is not None and self.column_start < 1:
            raise ValueError("column_start must be >= 1")

        if self.column_end is not None and self.column_end < 1:
            raise ValueError("column_end must be >= 1")
