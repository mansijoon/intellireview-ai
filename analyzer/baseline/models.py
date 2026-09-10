from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from analyzer.core.models import Finding


@dataclass(frozen=True, slots=True)
class BaselineFinding:
    fingerprint: str
    analyzer: str
    rule_id: str
    title: str
    severity: str
    file_path: str
    line_start: int
    line_end: int | None
    description: str

    @classmethod
    def from_finding(
        cls,
        finding: Finding,
        fingerprint: str,
    ) -> "BaselineFinding":
        return cls(
            fingerprint=fingerprint,
            analyzer=finding.analyzer,
            rule_id=finding.rule_id,
            title=finding.title,
            severity=(
                finding.severity.value
                if hasattr(finding.severity, "value")
                else str(finding.severity)
            ),
            file_path=finding.location.file_path,
            line_start=finding.location.line_start,
            line_end=finding.location.line_end,
            description=finding.description,
        )


@dataclass(frozen=True, slots=True)
class Baseline:
    repository_id: str
    revision: str
    repository_fingerprint: str
    created_at: str
    findings: tuple[BaselineFinding, ...] = field(
        default_factory=tuple
    )

    @classmethod
    def create(
        cls,
        *,
        repository_id: str,
        revision: str,
        repository_fingerprint: str,
        findings: tuple[BaselineFinding, ...],
    ) -> "Baseline":
        return cls(
            repository_id=repository_id,
            revision=revision,
            repository_fingerprint=repository_fingerprint,
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            findings=findings,
        )


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    repository_id: str
    baseline_revision: str
    current_revision: str
    new_findings: tuple[BaselineFinding, ...]
    resolved_findings: tuple[BaselineFinding, ...]
    unchanged_findings: tuple[BaselineFinding, ...]

    @property
    def new_count(self) -> int:
        return len(self.new_findings)

    @property
    def resolved_count(self) -> int:
        return len(self.resolved_findings)

    @property
    def unchanged_count(self) -> int:
        return len(self.unchanged_findings)

    @property
    def has_regressions(self) -> bool:
        return bool(self.new_findings)

    def to_dict(self) -> dict[str, Any]:
        def serialize(
            finding: BaselineFinding,
        ) -> dict[str, Any]:
            return {
                "fingerprint": finding.fingerprint,
                "analyzer": finding.analyzer,
                "rule_id": finding.rule_id,
                "title": finding.title,
                "severity": finding.severity,
                "file_path": finding.file_path,
                "line_start": finding.line_start,
                "line_end": finding.line_end,
                "description": finding.description,
            }

        return {
            "repository_id": self.repository_id,
            "baseline_revision": self.baseline_revision,
            "current_revision": self.current_revision,
            "new_findings": [
                serialize(finding)
                for finding in self.new_findings
            ],
            "resolved_findings": [
                serialize(finding)
                for finding in self.resolved_findings
            ],
            "unchanged_findings": [
                serialize(finding)
                for finding in self.unchanged_findings
            ],
            "summary": {
                "new": self.new_count,
                "resolved": self.resolved_count,
                "unchanged": self.unchanged_count,
                "has_regressions": self.has_regressions,
            },
        }
