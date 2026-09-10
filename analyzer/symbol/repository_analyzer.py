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
from analyzer.dependency.builder import build_dependency_graph
from analyzer.symbol.builder import build_symbol_graph
from analyzer.symbol.resolver import resolve_symbol_references
from analyzer.symbol.graph import get_symbol_counts


class SymbolRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide Python symbol analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="symbol",
            depends_on=frozenset({"dependency"}),
        source_sensitive=True,
        name="Symbol Analyzer",
        description=(
            "Builds a repository-wide symbol graph from "
            "cached Python ASTs."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        diagnostics: list[AnalysisDiagnostic] = []

        try:
            graph = build_symbol_graph(
                repository
            )

            dependency_graph = (
                repository.get_artifact(
                    "dependency_graph"
                )
            )

            if dependency_graph is None:
                dependency_graph = build_dependency_graph(
                    repository
                )

                repository.set_artifact(
                    "dependency_graph",
                    dependency_graph,
                )

            graph = resolve_symbol_references(
                graph,
                dependency_graph,
            )

            counts = get_symbol_counts(
                graph
            )

            artifacts = {
                "symbol_graph": graph,
                "symbol_count": graph.symbol_count,
                "reference_count": graph.reference_count,
                "module_count": counts.get(
                    "module",
                    0,
                ),
                "class_count": counts.get(
                    "class",
                    0,
                ),
                "function_count": counts.get(
                    "function",
                    0,
                ),
                "method_count": counts.get(
                    "method",
                    0,
                ),
                "symbol_counts": counts,
                "resolved_reference_count": sum(
                    reference.resolution_status.value
                    == "resolved"
                    for reference in graph.references
                ),
                "unresolved_reference_count": sum(
                    reference.resolution_status.value
                    == "unresolved"
                    for reference in graph.references
                ),
            }

            completed_at = datetime.now(
                timezone.utc
            )

            diagnostics.append(
                AnalysisDiagnostic(
                    message=(
                        "Symbol analysis completed successfully."
                    ),
                    severity="info",
                )
            )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts=artifacts,
                diagnostics=tuple(diagnostics),
            )

        except Exception as exc:
            completed_at = datetime.now(
                timezone.utc
            )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Symbol analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "symbol_analysis",
            result,
        )

        return result
