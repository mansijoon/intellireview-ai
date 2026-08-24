from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SBOMComponent:
    """A software component represented in the repository SBOM."""

    name: str
    version: str | None
    ecosystem: str
    package_url: str | None
    source_file: str
    dependency_type: str = "runtime"
    licenses: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class LicenseFinding:
    """A normalized dependency license finding."""

    package_name: str
    version: str | None
    license_id: str
    source: str
    source_file: str
    risk: str = "unknown"
    message: str = ""


@dataclass(slots=True)
class LicenseReport:
    """Repository-wide dependency license analysis."""

    component_count: int = 0
    licensed_component_count: int = 0
    unknown_license_count: int = 0
    restricted_license_count: int = 0
    findings: list[LicenseFinding] = field(
        default_factory=list
    )


@dataclass(slots=True)
class SBOMReport:
    """Repository software bill of materials."""

    format: str = "CycloneDX"
    spec_version: str = "1.5"
    component_count: int = 0
    components: list[SBOMComponent] = field(
        default_factory=list
    )
