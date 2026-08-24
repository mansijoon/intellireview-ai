from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .finding import Finding
from .repository import RepositorySnapshot


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Result produced by the IntelliReview analysis engine."""

    repository: RepositorySnapshot
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None

    @property
    def finding_count(self) -> int:
        return len(self.findings)
