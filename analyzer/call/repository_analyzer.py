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

from analyzer.call.builder import collect_call_relationships
from analyzer.call.models import CallGraph
from analyzer.call.resolver import resolve_call_relationships
from analyzer.dependency.builder import build_dependency_graph
from analyzer.symbol.builder import build_symbol_graph
from analyzer.symbol.resolver import resolve_symbol_references


class CallRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide call relationship analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="call",
            depends_on=frozenset({"dependency", "symbol"}),
        source_sensitive=False,
        name="Call Analyzer",
        description=(
            "Builds and resolves repository-wide call "
            "relationships using cached ASTs, symbols, "
            "and dependency information."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            dependency_graph = repository.get_artifact(
                "dependency_graph"
            )

            if dependency_graph is None:
                dependency_graph = build_dependency_graph(
                    repository
                )
                repository.set_artifact(
                    "dependency_graph",
                    dependency_graph,
                )

            symbol_graph = repository.get_artifact(
                "symbol_graph"
            )

            if symbol_graph is None:
                symbol_graph = build_symbol_graph(
                    repository
                )

                resolve_symbol_references(
                    symbol_graph,
                    dependency_graph,
                )

                repository.set_artifact(
                    "symbol_graph",
                    symbol_graph,
                )

            call_graph = CallGraph()

            for source_file in repository.files:
                if source_file.language.lower() not in {
                    "python",
                    "py",
                }:
                    continue

                context = repository.get_context(
                    source_file.path
                )

                tree = context.ast_tree

                if tree is None:
                    continue

                partial = collect_call_relationships(
                    symbol_graph,
                    source_file.path,
                    tree,
                )

                call_graph.calls.extend(
                    partial.calls
                )

            source_by_file = {
                source_file.path: repository.get_context(
                    source_file.path
                ).source
                for source_file in repository.files
                if source_file.language.lower()
                in {"python", "py"}
            }

            resolve_call_relationships(
                call_graph,
                symbol_graph,
                dependency_graph,
                source_by_file=source_by_file,
            )

            completed_at = datetime.now(timezone.utc)

            repository.set_artifact(
                "call_graph",
                call_graph,
            )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "call_graph": call_graph,
                    "call_count": call_graph.call_count,
                    "resolved_call_count": (
                        call_graph.resolved_call_count
                    ),
                    "unresolved_call_count": (
                        call_graph.unresolved_call_count
                    ),
                },
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Call analysis completed successfully."
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
                            "Call analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "call_analysis",
            result,
        )

        return result
