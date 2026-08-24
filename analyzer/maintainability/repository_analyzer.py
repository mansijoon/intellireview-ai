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
from analyzer.maintainability.models import (
    FileMaintainability,
    MaintainabilityReport,
)


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


class MaintainabilityRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic maintainability analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="maintainability",
        name="Maintainability Analyzer",
        description=(
            "Computes repository-wide maintainability scores "
            "from canonical static findings and complexity metrics."
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
                    "Static analysis artifact is required "
                    "for maintainability analysis."
                )

            complexity_result = repository.get_artifact(
                "complexity_analysis"
            )

            if complexity_result is None:
                raise RuntimeError(
                    "Complexity analysis artifact is required "
                    "for maintainability analysis."
                )

            findings = static_result.artifacts.get(
                "findings",
                (),
            )

            complexity_files = (
                complexity_result.artifacts.get(
                    "file_complexities",
                    (),
                )
            )

            findings_by_file: dict[str, int] = {}

            for finding in findings:
                file_path = finding.location.file_path

                findings_by_file[file_path] = (
                    findings_by_file.get(
                        file_path,
                        0,
                    )
                    + 1
                )

            files: list[FileMaintainability] = []

            for metrics in complexity_files:
                issue_count = findings_by_file.get(
                    metrics.file_path,
                    0,
                )

                score = 100

                score -= issue_count * 5
                score -= metrics.cyclomatic_complexity * 2

                if metrics.lines_of_code > 500:
                    score -= 10

                score = max(
                    0,
                    min(100, score),
                )

                files.append(
                    FileMaintainability(
                        file_path=metrics.file_path,
                        score=score,
                        grade=_grade(score),
                        issue_count=issue_count,
                        complexity=(
                            metrics.cyclomatic_complexity
                        ),
                        lines_of_code=(
                            metrics.lines_of_code
                        ),
                    )
                )

            ordered_files = tuple(
                sorted(
                    files,
                    key=lambda item: (
                        item.score,
                        item.file_path,
                    ),
                )
            )

            average_score = (
                round(
                    sum(
                        item.score
                        for item in files
                    )
                    / len(files),
                    2,
                )
                if files
                else 0.0
            )

            repository_grade = _grade(
                round(average_score)
            )

            report = MaintainabilityReport(
                file_count=len(files),
                average_score=average_score,
                grade=repository_grade,
                files=ordered_files,
                lowest_scoring_files=(
                    ordered_files[:10]
                ),
            )

            artifacts = {
                "maintainability_report": report,
                "file_maintainability": ordered_files,
                "file_count": report.file_count,
                "average_score": report.average_score,
                "grade": report.grade,
                "lowest_scoring_files": (
                    report.lowest_scoring_files
                ),
            }

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Maintainability analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Maintainability analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "maintainability_analysis",
            result,
        )

        return result
