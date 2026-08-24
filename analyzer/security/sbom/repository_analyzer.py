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
from analyzer.core.repository_context import RepositoryContext

from analyzer.security.sbom.analyzer import (
    analyze_sbom_and_licenses,
)
from analyzer.security.sbom.cyclonedx import (
    sbom_to_cyclonedx,
    sbom_to_cyclonedx_json,
)


class SBOMRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide SBOM and license analyzer."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="sbom",
        name="SBOM and License Analyzer",
        description=(
            "Builds a repository software bill of materials "
            "and evaluates dependency license metadata."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            sbom_report, license_report = (
                analyze_sbom_and_licenses(
                    repository.root_path
                )
            )

            cyclonedx = sbom_to_cyclonedx(
                sbom_report
            )

            cyclonedx_json = (
                sbom_to_cyclonedx_json(
                    sbom_report
                )
            )

            artifacts = {
                "sbom_report": sbom_report,
                "sbom": cyclonedx,
                "sbom_json": cyclonedx_json,
                "license_report": license_report,
                "component_count": (
                    sbom_report.component_count
                ),
                "license_count": len(
                    license_report.findings
                ),
                "unknown_license_count": (
                    license_report.unknown_license_count
                ),
                "restricted_license_count": (
                    license_report.restricted_license_count
                ),
            }

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(
                    timezone.utc
                ),
                artifacts=artifacts,
                diagnostics=(),
            )

            repository.set_artifact(
                "sbom_analysis",
                result,
            )

            return result

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(
                    timezone.utc
                ),
                artifacts={},
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            f"SBOM analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                        file_path=None,
                    ),
                ),
            )

            repository.set_artifact(
                "sbom_analysis",
                result,
            )

            return result
