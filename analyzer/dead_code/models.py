from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FileDeadCode:
    file_path: str
    finding_count: int


@dataclass(frozen=True, slots=True)
class DeadCodeReport:
    finding_count: int
    affected_file_count: int
    file_count: int
    dead_code_percentage: float
    files: tuple[FileDeadCode, ...] = field(
        default_factory=tuple
    )
