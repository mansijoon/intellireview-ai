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

from analyzer.performance.models import (
    PerformanceFileReport,
    PerformanceReport,
)
from analyzer.performance.rules import (
    DEFAULT_PERFORMANCE_RULES,
)


class PerformanceRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic performance analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="performance",
        name="Performance Analyzer",
        description=(
            "Detects statically identifiable performance risks "
            "across supported repository source files."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            rules = tuple(
                rule_class()
                for rule_class in DEFAULT_PERFORMANCE_RULES
            )

            file_reports: list[PerformanceFileReport] = []

            for context in repository.iter_contexts():
                findings = []

                if context.language.lower() != "python":
                    continue

                for rule in rules:
                    findings.extend(
                        rule.analyze(context)
                    )

                if findings:
                    file_reports.append(
                        PerformanceFileReport(
                            file_path=context.file_path,
                            finding_count=len(findings),
                            findings=tuple(findings),
                        )
                    )

            affected_file_count = len(file_reports)
            finding_count = sum(
                item.finding_count
                for item in file_reports
            )

            report = PerformanceReport(
                file_count=repository.file_count,
                affected_file_count=affected_file_count,
                finding_count=finding_count,
                files=tuple(file_reports),
            )

            artifacts = {
                "performance_report": report,
                "finding_count": report.finding_count,
                "affected_file_count": (
                    report.affected_file_count
                ),
                "performance_percentage": (
                    round(
                        (
                            affected_file_count
                            / repository.file_count
                            * 100
                        )
                        if repository.file_count
                        else 0.0,
                        2,
                    )
                ),
                "files": report.files,
                "rule_count": len(rules),
            }

            result = RepositoryAnalysisResult(
                analyzer_id="performance",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Performance analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "performance_analysis",
                result,
            )

            return result

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id="performance",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Performance analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "performance_analysis",
                result,
            )

            return result
