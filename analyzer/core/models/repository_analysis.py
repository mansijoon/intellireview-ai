from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class RepositoryAnalysisStatus(StrEnum):
    """Execution status of a repository analyzer."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AnalysisDiagnostic:
    """Diagnostic describing an analyzer execution issue."""

    message: str
    severity: str = "warning"
    file_path: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError(
                "diagnostic message must not be empty"
            )


@dataclass(frozen=True, slots=True)
class RepositoryAnalysisResult:
    """Structured result produced by one repository analyzer."""

    analyzer_id: str
    status: RepositoryAnalysisStatus

    started_at: datetime
    completed_at: datetime

    artifacts: dict[str, Any] = field(
        default_factory=dict
    )

    diagnostics: tuple[AnalysisDiagnostic, ...] = field(
        default_factory=tuple
    )

    @property
    def duration_ms(self) -> float:
        """Analyzer execution duration in milliseconds."""

        return (
            self.completed_at - self.started_at
        ).total_seconds() * 1000

    def __post_init__(self) -> None:
        if not self.analyzer_id.strip():
            raise ValueError(
                "analyzer_id must not be empty"
            )

        if self.completed_at < self.started_at:
            raise ValueError(
                "completed_at must be >= started_at"
            )
