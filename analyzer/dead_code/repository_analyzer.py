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

from analyzer.dead_code.models import (
    DeadCodeReport,
    FileDeadCode,
)


class DeadCodeRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide dead-code analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="dead_code",
        name="Dead Code Analyzer",
        description=(
            "Aggregates canonical dead-function findings "
            "into repository-level dead-code metrics."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            static_result = repository.get_artifact(
                "static_analysis"
            )

            if static_result is None:
                raise RuntimeError(
                    "Static analysis result is required "
                    "before dead-code analysis."
                )

            findings = tuple(
                finding
                for finding in static_result.artifacts.get(
                    "findings",
                    (),
                )
                if finding.rule_id == "PY-DEAD-001"
            )

            by_file: dict[str, int] = {}

            for finding in findings:
                file_path = finding.location.file_path

                by_file[file_path] = (
                    by_file.get(file_path, 0) + 1
                )

            files = tuple(
                FileDeadCode(
                    file_path=file_path,
                    finding_count=count,
                )
                for file_path, count in sorted(
                    by_file.items(),
                    key=lambda item: (
                        -item[1],
                        item[0],
                    ),
                )
            )

            file_count = repository.file_count
            affected_file_count = len(files)

            dead_code_percentage = (
                round(
                    (
                        affected_file_count
                        / file_count
                    ) * 100,
                    2,
                )
                if file_count
                else 0.0
            )

            report = DeadCodeReport(
                finding_count=len(findings),
                affected_file_count=(
                    affected_file_count
                ),
                file_count=file_count,
                dead_code_percentage=(
                    dead_code_percentage
                ),
                files=files,
            )

            artifacts = {
                "dead_code_report": report,
                "findings": findings,
                "finding_count": len(findings),
                "affected_file_count": (
                    affected_file_count
                ),
                "dead_code_percentage": (
                    dead_code_percentage
                ),
                "files": files,
            }

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="dead_code",
                status=(
                    RepositoryAnalysisStatus.SUCCESS
                ),
                started_at=started_at,
                completed_at=completed_at,
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dead-code analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "dead_code_analysis",
                result,
            )

            return result

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="dead_code",
                status=(
                    RepositoryAnalysisStatus.FAILED
                ),
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dead-code analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "dead_code_analysis",
                result,
            )

            return result
