from __future__ import annotations

from datetime import datetime, timezone

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import (
    RepositoryContext,
)

from analyzer.security.dependency.manifest import (
    extract_dependencies,
)
from analyzer.security.dependency.models import (
    DependencyVulnerability,
    DependencyVulnerabilityReport,
    VulnerabilityAdvisory,
)
from analyzer.security.dependency.osv import (
    query_osv_batch,
)


class DependencyVulnerabilityRepositoryAnalyzer(
    RepositoryAnalyzer
):
    """Repository-wide third-party dependency vulnerability analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="dependency_vulnerability",
        name="Dependency Vulnerability Analyzer",
        description=(
            "Extracts Python dependencies and checks "
            "resolved versions against OSV advisories."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            dependencies = extract_dependencies(
                repository.root_path
            )

            advisory_data = repository.configuration.get(
                "security:dependency_advisories"
            )

            if advisory_data is not None:
                vulnerabilities = self._match_injected_advisories(
                    dependencies,
                    advisory_data,
                )
            else:
                vulnerabilities = (
                    self._query_osv(
                        dependencies
                    )
                )

            report = (
                DependencyVulnerabilityReport(
                    dependency_count=len(
                        dependencies
                    ),
                    vulnerable_dependency_count=len(
                        {
                            vulnerability.dependency.name
                            for vulnerability
                            in vulnerabilities
                        }
                    ),
                    vulnerability_count=len(
                        vulnerabilities
                    ),
                    dependencies=dependencies,
                    vulnerabilities=vulnerabilities,
                )
            )

            artifacts = {
                "dependency_vulnerability_report": report,
                "dependencies": tuple(
                    dependencies
                ),
                "vulnerabilities": tuple(
                    vulnerabilities
                ),
                "dependency_count": (
                    report.dependency_count
                ),
                "vulnerable_dependency_count": (
                    report.vulnerable_dependency_count
                ),
                "vulnerability_count": (
                    report.vulnerability_count
                ),
            }

            result = RepositoryAnalysisResult(
                analyzer_id=(
                    "dependency_vulnerability"
                ),
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(
                    timezone.utc
                ),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dependency vulnerability "
                            "analysis completed successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "dependency_vulnerability_analysis",
                result,
            )

            return result

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id=(
                    "dependency_vulnerability"
                ),
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(
                    timezone.utc
                ),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dependency vulnerability "
                            f"analysis failed: {exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "dependency_vulnerability_analysis",
                result,
            )

            return result

    @staticmethod
    def _query_osv(
        dependencies,
    ) -> list[DependencyVulnerability]:
        results = query_osv_batch(
            dependencies
        )

        vulnerabilities = []

        for dependency in dependencies:
            advisories = results.get(
                (
                    dependency.name,
                    dependency.version,
                ),
                (),
            )

            for advisory in advisories:
                vulnerabilities.append(
                    DependencyVulnerability(
                        dependency=dependency,
                        advisory=advisory,
                    )
                )

        return vulnerabilities

    @staticmethod
    def _match_injected_advisories(
        dependencies,
        advisories,
    ) -> list[DependencyVulnerability]:
        vulnerabilities = []

        for dependency in dependencies:
            for advisory in advisories:
                if not isinstance(
                    advisory,
                    VulnerabilityAdvisory,
                ):
                    continue

                if (
                    advisory.package_name.lower()
                    != dependency.name.lower()
                ):
                    continue

                vulnerabilities.append(
                    DependencyVulnerability(
                        dependency=dependency,
                        advisory=advisory,
                    )
                )

        return vulnerabilities
