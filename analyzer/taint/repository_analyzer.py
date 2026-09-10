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

from analyzer.taint.engine import analyze_taint
from analyzer.taint.interprocedural import (
    analyze_interprocedural_taint,
)
from analyzer.taint.repository_graphs import (
    ensure_taint_graphs,
)


class TaintRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide Python taint/source-to-sink analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="taint",
            depends_on=frozenset({"dependency", "symbol", "call"}),
        source_sensitive=True,
        name="Taint Analyzer",
        description=(
            "Tracks statically identifiable tainted data "
            "from sources through local propagation and "
            "resolved function boundaries to security-sensitive sinks."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            # Taint must not depend on registry execution order.
            ensure_taint_graphs(repository)

            findings: list[Finding] = []
            paths = []

            source_count = 0
            sink_count = 0
            analyzed_file_count = 0

            # ---------------------------------------------------------
            # Local / intra-procedural taint analysis
            # ---------------------------------------------------------
            for context in repository.iter_contexts():
                if context.language.lower() not in {
                    "python",
                    "py",
                }:
                    continue

                analyzed_file_count += 1

                report, file_findings = analyze_taint(
                    context
                )

                source_count += report.source_count
                sink_count += report.sink_count

                findings.extend(
                    file_findings
                )

                paths.extend(
                    report.paths
                )

            # ---------------------------------------------------------
            # Interprocedural taint analysis
            # ---------------------------------------------------------
            (
                interprocedural_paths,
                interprocedural_findings,
                interprocedural_bindings,
            ) = analyze_interprocedural_taint(
                repository
            )

            findings.extend(
                interprocedural_findings
            )

            paths.extend(
                interprocedural_paths
            )

            affected_file_count = len(
                {
                    finding.location.file_path
                    for finding in findings
                }
            )

            artifacts = {
                "findings": findings,
                "taint_findings": findings,
                "paths": paths,
                "interprocedural_paths": (
                    interprocedural_paths
                ),
                "finding_count": len(findings),
                "affected_file_count": (
                    affected_file_count
                ),
                "source_count": source_count,
                "sink_count": sink_count,
                "analyzed_file_count": (
                    analyzed_file_count
                ),
                "rule_count": 2,
                "interprocedural_binding_count": (
                    len(interprocedural_bindings)
                ),
            }

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="taint",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Taint analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="taint",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Taint analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "taint_analysis",
            result,
        )

        return result
