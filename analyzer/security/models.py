from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from analyzer.core.models import SourceLocation


class SecurityCategory(StrEnum):
    """Security analysis category."""

    SAST = "sast"
    SECRET = "secret"
    DATA_FLOW = "data_flow"
    TAINT = "taint"
    DEPENDENCY = "dependency"
    LICENSE = "license"


class SecurityVerificationStatus(StrEnum):
    """Verification state of a security finding."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    DISMISSED = "dismissed"


class SecuritySeverity(StrEnum):
    """Security severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SecurityEvidence:
    """Evidence supporting a security finding."""

    location: SourceLocation
    message: str
    role: str = "evidence"


@dataclass(frozen=True, slots=True)
class SecuritySource:
    """Potential taint/data-flow source."""

    source_id: str
    name: str
    location: SourceLocation
    category: str


@dataclass(frozen=True, slots=True)
class SecuritySink:
    """Potential security-sensitive sink."""

    sink_id: str
    name: str
    location: SourceLocation
    category: str


@dataclass(frozen=True, slots=True)
class SecurityFinding:
    """Security-specific metadata attached to a canonical finding."""

    rule_id: str
    category: SecurityCategory
    severity: SecuritySeverity
    confidence: float
    verification_status: SecurityVerificationStatus = (
        SecurityVerificationStatus.UNVERIFIED
    )

    source: SecuritySource | None = None
    sink: SecuritySink | None = None

    evidence: tuple[SecurityEvidence, ...] = field(
        default_factory=tuple
    )

    remediation: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass(frozen=True, slots=True)
class SecurityRiskReport:
    """Repository-level security risk summary."""

    score: float
    severity_counts: dict[str, int]
    verified_count: int
    unverified_count: int
    finding_count: int


@dataclass(slots=True)
class SecurityAnalysisReport:
    """Repository-wide security analysis result."""

    file_count: int = 0
    finding_count: int = 0
    affected_file_count: int = 0

    findings: list[SecurityFinding] = field(
        default_factory=list
    )

    risk_report: SecurityRiskReport | None = None
