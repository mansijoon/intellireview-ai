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
            depends_on=frozenset(),
        source_sensitive=True,
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

            rules = [
                rule
                for rule in registry.create_rules()
                if rule.metadata.category != "security"
            ]

            cache = repository.configuration.get(
                "_intellireview_analysis_cache"
            )

            findings: list[Finding] = []
            rule_counts: dict[str, int] = {}

            supported_languages = {
                "python",
                "py",
            }

            analyzed_file_count = 0

            scope = repository.analysis_scope

            for source_file in repository.files:
                if source_file.language.lower() not in supported_languages:
                    continue

                analyzed_file_count += 1

                is_in_scope = (
                    scope is None
                    or source_file.path in scope
                )

                context = None

                if is_in_scope:
                    context = repository.get_context(
                        source_file.path
                    )

                for rule in rules:
                    cached = None

                    if cache is not None:
                        cached = cache.get_file_result(
                            self.metadata.analyzer_id,
                            source_file.path,
                            source_file.content_hash,
                            variant=rule.metadata.rule_id,
                        )

                    if isinstance(cached, tuple):
                        rule_findings = [
                            finding
                            for finding in cached
                            if isinstance(finding, Finding)
                        ]
                    elif not is_in_scope:
                        rule_findings = []
                    else:
                        rule_findings = rule.analyze(context)

                        if cache is not None:
                            cache.set_file_result(
                                self.metadata.analyzer_id,
                                source_file.path,
                                source_file.content_hash,
                                tuple(rule_findings),
                                variant=rule.metadata.rule_id,
                            )

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
