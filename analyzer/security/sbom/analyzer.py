from __future__ import annotations

from analyzer.security.dependency.manifest import (
    extract_dependencies,
)
from analyzer.security.sbom.licenses import (
    classify_license,
)
from analyzer.security.sbom.metadata import (
    resolve_package_metadata,
)
from analyzer.security.sbom.models import (
    LicenseFinding,
    LicenseReport,
    SBOMComponent,
    SBOMReport,
)


def analyze_sbom_and_licenses(
    repository_root: str,
) -> tuple[
    SBOMReport,
    LicenseReport,
]:
    """Build a repository SBOM and analyze dependency licenses."""

    dependencies = extract_dependencies(
        repository_root
    )

    components: list[SBOMComponent] = []
    findings: list[LicenseFinding] = []

    for dependency in dependencies:
        component = resolve_package_metadata(
            dependency
        )

        components.append(component)

        if not component.licenses:
            findings.append(
                LicenseFinding(
                    package_name=component.name,
                    version=component.version,
                    license_id="UNKNOWN",
                    source="package-metadata",
                    source_file=component.source_file,
                    risk="unknown",
                    message=(
                        "No license metadata was "
                        "resolved for this dependency."
                    ),
                )
            )

            continue

        for license_id in component.licenses:
            risk = classify_license(
                license_id
            )

            findings.append(
                LicenseFinding(
                    package_name=component.name,
                    version=component.version,
                    license_id=license_id,
                    source="package-metadata",
                    source_file=component.source_file,
                    risk=risk,
                    message=(
                        f"License classified as {risk}."
                    ),
                )
            )

    licensed_count = sum(
        bool(component.licenses)
        for component in components
    )

    unknown_count = sum(
        finding.license_id == "UNKNOWN"
        for finding in findings
    )

    restricted_count = sum(
        finding.risk == "strong-copyleft"
        for finding in findings
    )

    sbom_report = SBOMReport(
        format="CycloneDX",
        spec_version="1.5",
        component_count=len(
            components
        ),
        components=components,
    )

    license_report = LicenseReport(
        component_count=len(
            components
        ),
        licensed_component_count=(
            licensed_count
        ),
        unknown_license_count=(
            unknown_count
        ),
        restricted_license_count=(
            restricted_count
        ),
        findings=findings,
    )

    return (
        sbom_report,
        license_report,
    )
