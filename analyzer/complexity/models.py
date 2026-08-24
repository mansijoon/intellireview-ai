from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileComplexity:
    """Complexity metrics for one repository source file."""

    file_path: str
    language: str
    lines_of_code: int
    cyclomatic_complexity: int
    complexity_score: float
    function_count: int
    class_count: int
    import_count: int


@dataclass(frozen=True, slots=True)
class ComplexityReport:
    """Repository-wide complexity summary."""

    file_count: int
    total_lines: int
    total_functions: int
    total_classes: int
    total_imports: int
    total_cyclomatic_complexity: int
    average_complexity: float
    high_complexity_files: tuple[FileComplexity, ...]
    files: tuple[FileComplexity, ...]
