from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .evidence import Evidence
from .location import SourceLocation


class Severity(StrEnum):
    """Normalized finding severity."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(StrEnum):
    """Verification state of a finding."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Finding:
    """Canonical representation of an IntelliReview finding."""

    rule_id: str
    title: str
    description: str
    severity: Severity
    location: SourceLocation
    analyzer: str

    confidence: float = 1.0
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    remediation: str | None = None
    suggested_patch: str | None = None

    references: tuple[str, ...] = field(default_factory=tuple)

    fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")

        if not self.title.strip():
            raise ValueError("title must not be empty")

        if not self.description.strip():
            raise ValueError("description must not be empty")

        if not self.analyzer.strip():
            raise ValueError("analyzer must not be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
