from __future__ import annotations

from datetime import datetime, timezone

from analyzer.call.models import (
    CallGraph,
    CallResolutionStatus,
)
from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    Finding,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
    Severity,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.dead_code.models import (
    DeadCodeReport,
    FileDeadCode,
)
from analyzer.symbol.models import SymbolGraph


class DeadCodeRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide dead-code analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="dead_code",
            depends_on=frozenset({"symbol", "call"}),
        source_sensitive=False,
        name="Dead Code Analyzer",
        description=(
            "Detects functions and methods with no "
            "statically resolved incoming calls."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            symbol_graph = repository.get_artifact(
                "symbol_graph"
            )

            if symbol_graph is None:
                raise RuntimeError(
                    "Symbol graph is required before "
                    "dead-code analysis."
                )

            call_graph = repository.get_artifact(
                "call_graph"
            )

            if call_graph is None:
                raise RuntimeError(
                    "Call graph is required before "
                    "dead-code analysis."
                )

            if not isinstance(symbol_graph, SymbolGraph):
                raise TypeError(
                    "symbol_graph artifact has an unexpected type."
                )

            if not isinstance(call_graph, CallGraph):
                raise TypeError(
                    "call_graph artifact has an unexpected type."
                )

            findings: list[Finding] = []

            for symbol in symbol_graph.symbols.values():
                if symbol.kind not in {
                    "function",
                    "method",
                }:
                    continue

                if symbol.name == "main":
                    continue

                incoming_calls = call_graph.calls_to(
                    symbol.symbol_id
                )

                resolved_incoming_calls = tuple(
                    call
                    for call in incoming_calls
                    if (
                        call.resolution_status
                        == CallResolutionStatus.RESOLVED
                    )
                )

                if resolved_incoming_calls:
                    continue

                findings.append(
                    Finding(
                        rule_id="PY-DEAD-001",
                        title="Dead Function",
                        description=(
                            f"{symbol.name} defined but "
                            "has no statically resolved "
                            "incoming calls."
                        ),
                        severity=Severity.MEDIUM,
                        location=symbol.location,
                        analyzer="dead_code",
                        confidence=1.0,
                    )
                )

            findings.sort(
                key=lambda finding: (
                    finding.location.file_path,
                    finding.location.line_start,
                    finding.location.line_end,
                    finding.description,
                )
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
                affected_file_count=affected_file_count,
                file_count=file_count,
                dead_code_percentage=dead_code_percentage,
                files=files,
            )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "dead_code_report": report,
                    "findings": tuple(findings),
                    "finding_count": len(findings),
                    "affected_file_count": (
                        affected_file_count
                    ),
                    "dead_code_percentage": (
                        dead_code_percentage
                    ),
                    "files": files,
                },
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
