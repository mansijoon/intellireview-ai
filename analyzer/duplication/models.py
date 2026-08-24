from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class FileDuplication:
    file_path: str
    finding_count: int


@dataclass(frozen=True, slots=True)
class DuplicationReport:
    finding_count: int
    affected_file_count: int
    file_count: int
    duplication_percentage: float
    files: tuple[FileDuplication, ...] = field(
        default_factory=tuple
    )
