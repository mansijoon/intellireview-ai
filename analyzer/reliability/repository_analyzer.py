from __future__ import annotations

import ast
from datetime import datetime, timezone

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
    Evidence,
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


def _find_ast_node(
    context: RepositoryContext,
    item: dict,
) -> ast.AST | None:
    """Find the exception-handler AST node represented by a finding."""

    tree = context.ast_tree

    if tree is None:
        return None

    line_start = item["line_start"]
    line_end = item["line_end"]

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue

        node_line_start = getattr(
            node,
            "lineno",
            None,
        )

        node_line_end = getattr(
            node,
            "end_lineno",
            node_line_start,
        )

        if (
            node_line_start == line_start
            and node_line_end == line_end
        ):
            return node

    return None


class ReliabilityRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic reliability analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="reliability",
            depends_on=frozenset(),
        source_sensitive=True,
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

            cache = repository.configuration.get(
                "_intellireview_analysis_cache"
            )
            scope = repository.analysis_scope

            for context in repository.iter_contexts():
                if context.language.lower() != "python":
                    continue

                file_report = None

                if cache is not None:
                    cached = cache.get_file_result(
                        "reliability",
                        context.file_path,
                        context.content_hash,
                    )
                    if isinstance(
                        cached,
                        ReliabilityFileReport,
                    ):
                        file_report = cached

                if file_report is None:
                    if (
                        scope is not None
                        and context.file_path not in scope
                    ):
                        continue

                    raw_findings = []

                    for rule in rules:
                        raw_findings.extend(
                            rule.analyze(context)
                        )

                    reliability_findings = tuple(
                        ReliabilityFinding(
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
                        for item in raw_findings
                    )

                    file_report = ReliabilityFileReport(
                        file_path=context.file_path,
                        finding_count=len(
                            reliability_findings
                        ),
                        findings=reliability_findings,
                    )

                    if cache is not None:
                        cache.set_file_result(
                            "reliability",
                            context.file_path,
                            context.content_hash,
                            file_report,
                        )

                if file_report.finding_count:
                    file_reports.append(file_report)

                for item in file_report.findings:
                    location = SourceLocation(
                        file_path=item.file_path,
                        line_start=item.line_start,
                        line_end=item.line_end,
                    )

                    canonical_findings.append(
                        Finding(
                            rule_id=item.rule_id,
                            title=item.title,
                            description=item.description,
                            severity=Severity(
                                item.severity.lower()
                            ),
                            location=location,
                            analyzer="reliability",
                            confidence=item.confidence,
                            remediation=item.remediation,
                            evidence=(
                                (
                                    Evidence(
                                        message=(
                                            "Detected exception "
                                            "handler."
                                        ),
                                        location=location,
                                        code_snippet=(
                                            ast.get_source_segment(
                                                context.source,
                                                _find_ast_node(
                                                    context,
                                                    {
                                                        "line_start": (
                                                            item.line_start
                                                        ),
                                                        "line_end": (
                                                            item.line_end
                                                        ),
                                                    },
                                                ),
                                            )
                                        ),
                                    ),
                                )
                                if (
                                    context.file_path
                                    == item.file_path
                                    and _find_ast_node(
                                        context,
                                        {
                                            "line_start": item.line_start,
                                            "line_end": item.line_end,
                                        },
                                    )
                                    is not None
                                )
                                else ()
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
