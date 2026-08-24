from __future__ import annotations

from dataclasses import dataclass

from .location import SourceLocation


@dataclass(frozen=True, slots=True)
class Evidence:
    """Evidence supporting an analysis finding."""

    message: str
    location: SourceLocation | None = None
    code_snippet: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("evidence message must not be empty")
