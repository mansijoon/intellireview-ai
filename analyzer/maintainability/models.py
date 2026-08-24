from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileMaintainability:
    """Maintainability metrics for one repository source file."""

    file_path: str
    score: int
    grade: str
    issue_count: int
    complexity: int
    lines_of_code: int


@dataclass(frozen=True, slots=True)
class MaintainabilityReport:
    """Repository-wide maintainability summary."""

    file_count: int
    average_score: float
    grade: str
    files: tuple[FileMaintainability, ...]
    lowest_scoring_files: tuple[FileMaintainability, ...]
