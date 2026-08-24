from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReliabilityFinding:
    """One statically detected reliability risk."""

    rule_id: str
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    severity: str
    confidence: float
    remediation: str


@dataclass(frozen=True, slots=True)
class ReliabilityFileReport:
    """Reliability findings for one repository file."""

    file_path: str
    finding_count: int
    findings: tuple[ReliabilityFinding, ...]


@dataclass(frozen=True, slots=True)
class ReliabilityReport:
    """Repository-wide reliability analysis."""

    file_count: int
    affected_file_count: int
    finding_count: int
    files: tuple[ReliabilityFileReport, ...]
