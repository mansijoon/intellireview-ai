from __future__ import annotations

from dataclasses import dataclass

from analyzer.security.dependency.models import (
    DependencyVulnerability,
    PackageDependency,
    VulnerabilityAdvisory,
)


@dataclass(frozen=True, slots=True)
class AdvisoryProvider:
    """
    Supplies normalized vulnerability advisories.

    The provider is deliberately separated from matching so the
    analyzer can later support OSV, GitHub Advisory Database,
    offline advisory snapshots, or another source.
    """

    advisories: tuple[VulnerabilityAdvisory, ...]


def _package_matches(
    dependency: PackageDependency,
    advisory: VulnerabilityAdvisory,
) -> bool:
    return (
        dependency.name
        == advisory.package_name.lower()
    )


def match_vulnerabilities(
    dependencies: list[PackageDependency],
    provider: AdvisoryProvider,
) -> list[DependencyVulnerability]:
    vulnerabilities = []

    for dependency in dependencies:
        for advisory in provider.advisories:
            if not _package_matches(
                dependency,
                advisory,
            ):
                continue

            vulnerabilities.append(
                DependencyVulnerability(
                    dependency=dependency,
                    advisory=advisory,
                )
            )

    return vulnerabilities
