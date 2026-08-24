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
from analyzer.core.rules.defaults import create_default_registry


class StaticRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic static analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="static",
        name="Static Analyzer",
        description=(
            "Runs the canonical deterministic rule engine "
            "across supported repository source files."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            registry = create_default_registry()
            rules = registry.create_rules()

            findings: list[Finding] = []
            rule_counts: dict[str, int] = {}

            supported_languages = {
                "python",
                "py",
            }

            analyzed_file_count = 0

            for context in repository.iter_contexts():
                if context.language.lower() not in supported_languages:
                    continue

                analyzed_file_count += 1

                for rule in rules:
                    rule_findings = rule.analyze(context)

                    findings.extend(rule_findings)

                    rule_id = rule.metadata.rule_id

                    rule_counts[rule_id] = (
                        rule_counts.get(rule_id, 0)
                        + len(rule_findings)
                    )

            severity_counts: dict[str, int] = {}

            for finding in findings:
                severity = finding.severity

                severity_counts[severity] = (
                    severity_counts.get(severity, 0)
                    + 1
                )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "findings": tuple(findings),
                    "finding_count": len(findings),
                    "rule_count": len(rules),
                    "rule_counts": rule_counts,
                    "severity_counts": severity_counts,
                    "analyzed_file_count": analyzed_file_count,
                },
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Static analysis completed successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Static analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "static_analysis",
            result,
        )

        return result
