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
    Finding,
    Severity,
    SourceLocation,
)
from analyzer.core.repository_context import RepositoryContext

from analyzer.reliability.models import (
    ReliabilityFileReport,
    ReliabilityFinding,
    ReliabilityReport,
)
from analyzer.reliability.rules import (
    DEFAULT_RELIABILITY_RULES,
)


class ReliabilityRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic reliability analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="reliability",
        name="Reliability Analyzer",
        description=(
            "Detects statically identifiable exception-handling "
            "and failure-propagation risks across the repository."
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
                for rule_class in DEFAULT_RELIABILITY_RULES
            )

            file_reports: list[ReliabilityFileReport] = []
            canonical_findings: list[Finding] = []

            for context in repository.iter_contexts():
                if context.language.lower() != "python":
                    continue

                raw_findings = []

                for rule in rules:
                    raw_findings.extend(
                        rule.analyze(context)
                    )

                reliability_findings = []

                for item in raw_findings:
                    finding = ReliabilityFinding(
                        rule_id=item["rule_id"],
                        title=item["title"],
                        description=item["description"],
                        file_path=context.file_path,
                        line_start=item["line_start"],
                        line_end=item["line_end"],
                        severity=item["severity"],
                        confidence=item["confidence"],
                        remediation=item["remediation"],
                    )

                    reliability_findings.append(
                        finding
                    )

                    canonical_findings.append(
                        Finding(
                            rule_id=item["rule_id"],
                            title=item["title"],
                            description=item["description"],
                            severity=Severity(
                                item["severity"].lower()
                            ),
                            location=SourceLocation(
                                file_path=context.file_path,
                                line_start=item["line_start"],
                                line_end=item["line_end"],
                            ),
                            analyzer="reliability",
                            confidence=item["confidence"],
                            remediation=item["remediation"],
                        )
                    )

                if reliability_findings:
                    file_reports.append(
                        ReliabilityFileReport(
                            file_path=context.file_path,
                            finding_count=len(
                                reliability_findings
                            ),
                            findings=tuple(
                                reliability_findings
                            ),
                        )
                    )

            affected_file_count = len(file_reports)

            finding_count = sum(
                item.finding_count
                for item in file_reports
            )

            report = ReliabilityReport(
                file_count=repository.file_count,
                affected_file_count=affected_file_count,
                finding_count=finding_count,
                files=tuple(file_reports),
            )

            artifacts = {
                "reliability_report": report,
                "finding_count": finding_count,
                "affected_file_count": affected_file_count,
                "reliability_percentage": round(
                    (
                        affected_file_count
                        / repository.file_count
                        * 100
                    )
                    if repository.file_count
                    else 0.0,
                    2,
                ),
                "files": report.files,
                "findings": tuple(canonical_findings),
                "rule_count": len(rules),
            }

            result = RepositoryAnalysisResult(
                analyzer_id="reliability",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Reliability analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "reliability_analysis",
                result,
            )

            return result

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id="reliability",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Reliability analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "reliability_analysis",
                result,
            )

            return result
