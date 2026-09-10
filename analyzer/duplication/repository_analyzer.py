from __future__ import annotations

from datetime import datetime, timezone

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    Finding,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext

from analyzer.duplication.models import (
    DuplicationReport,
    FileDuplication,
)


class DuplicationRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide duplication analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="duplication",
            depends_on=frozenset({"static"}),
        source_sensitive=False,
        name="Duplication Analyzer",
        description=(
            "Aggregates canonical duplicate-code findings "
            "into repository-level duplication metrics."
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
                    "before duplication analysis."
                )

            findings = tuple(
                finding
                for finding in static_result.artifacts.get(
                    "findings",
                    ()
                )
                if finding.rule_id == "PY-DUP-001"
            )

            by_file: dict[str, int] = {}

            for finding in findings:
                file_path = finding.location.file_path
                by_file[file_path] = (
                    by_file.get(file_path, 0) + 1
                )

            files = tuple(
                FileDuplication(
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

            duplication_percentage = (
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

            report = DuplicationReport(
                finding_count=len(findings),
                affected_file_count=(
                    affected_file_count
                ),
                file_count=file_count,
                duplication_percentage=(
                    duplication_percentage
                ),
                files=files,
            )

            artifacts = {
                "duplication_report": report,
                "finding_count": len(findings),
                "affected_file_count": (
                    affected_file_count
                ),
                "duplication_percentage": (
                    duplication_percentage
                ),
                "files": files,
            }

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="duplication",
                status=(
                    RepositoryAnalysisStatus.SUCCESS
                ),
                started_at=started_at,
                completed_at=completed_at,
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Duplication analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "duplication_analysis",
                result,
            )

            return result

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="duplication",
                status=(
                    RepositoryAnalysisStatus.FAILED
                ),
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Duplication analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "duplication_analysis",
                result,
            )

            return result
