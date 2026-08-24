from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.security.models import (
    SecuritySeverity,
    SecurityVerificationStatus,
)


@dataclass(frozen=True, slots=True)
class PackageDependency:
    """A third-party package declared by the repository."""

    name: str
    version: str | None
    source_file: str
    dependency_type: str = "runtime"


@dataclass(frozen=True, slots=True)
class VulnerabilityAdvisory:
    """Normalized vulnerability advisory."""

    advisory_id: str
    package_name: str
    severity: SecuritySeverity
    summary: str
    affected_versions: tuple[str, ...] = field(
        default_factory=tuple
    )
    fixed_versions: tuple[str, ...] = field(
        default_factory=tuple
    )
    aliases: tuple[str, ...] = field(
        default_factory=tuple
    )
    references: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class DependencyVulnerability:
    """A vulnerability matched against an installed/declared dependency."""

    dependency: PackageDependency
    advisory: VulnerabilityAdvisory
    verification_status: SecurityVerificationStatus = (
        SecurityVerificationStatus.UNVERIFIED
    )


@dataclass(slots=True)
class DependencyVulnerabilityReport:
    """Repository-wide dependency vulnerability result."""

    dependency_count: int = 0
    vulnerable_dependency_count: int = 0
    vulnerability_count: int = 0

    dependencies: list[PackageDependency] = field(
        default_factory=list
    )

    vulnerabilities: list[DependencyVulnerability] = field(
        default_factory=list
    )
