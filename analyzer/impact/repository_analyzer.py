from __future__ import annotations

from datetime import datetime, timezone

from analyzer.call.builder import collect_call_relationships
from analyzer.call.models import CallGraph
from analyzer.call.resolver import resolve_call_relationships
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

from analyzer.impact.models import (
    ChangeImpactGraph,
)
from analyzer.impact.traversal import (
    reverse_call_impact,
    reverse_dependency_impact,
    reverse_symbol_impact,
)


class ChangeImpactRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide change-impact analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="change_impact",
        name="Change Impact Analyzer",
        description=(
            "Determines modules, symbols, and calls affected "
            "by explicitly changed repository targets."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        diagnostics: list[AnalysisDiagnostic] = []

        try:
            changed_modules = {
                str(value)
                for value in repository.configuration.get(
                    "impact:changed_modules",
                    set(),
                )
            }

            changed_symbols = {
                str(value)
                for value in repository.configuration.get(
                    "impact:changed_symbols",
                    set(),
                )
            }

            dependency_graph = (
                repository.get_artifact("dependency_graph")
            )

            if dependency_graph is None:
                dependency_graph = build_dependency_graph(
                    repository
                )
                repository.set_artifact(
                    "dependency_graph",
                    dependency_graph,
                )

            symbol_graph = (
                repository.get_artifact("symbol_graph")
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

            call_graph = (
                repository.get_artifact("call_graph")
            )

            if call_graph is None:
                call_graph = CallGraph()

                source_by_file: dict[str, str] = {}

                for source_file in repository.files:
                    context = repository.get_context(
                        source_file.path
                    )

                    tree = context.ast_tree

                    if tree is None:
                        continue

                    source_by_file[
                        source_file.path
                    ] = context.source

                    partial = (
                        collect_call_relationships(
                            symbol_graph,
                            source_file.path,
                            tree,
                        )
                    )

                    call_graph.calls.extend(
                        partial.calls
                    )

                resolve_call_relationships(
                    call_graph,
                    symbol_graph,
                    dependency_graph,
                    source_by_file,
                )

                repository.set_artifact(
                    "call_graph",
                    call_graph,
                )

            module_impacts = reverse_dependency_impact(
                dependency_graph,
                changed_modules,
            )

            symbol_impacts = reverse_symbol_impact(
                symbol_graph,
                changed_symbols,
            )

            call_impacts = reverse_call_impact(
                call_graph,
                changed_symbols,
            )

            graph = ChangeImpactGraph(
                changed_targets=tuple(
                    sorted(
                        changed_modules
                        | changed_symbols
                    )
                ),
                impacted_modules=module_impacts,
                impacted_symbols=symbol_impacts,
                impacted_calls=call_impacts,
            )

            direct_count = (
                graph.direct_impact_count
            )

            transitive_count = (
                graph.transitive_impact_count
            )

            impact_score = (
                direct_count * 2
                + transitive_count
            )

            artifacts = {
                "impact_graph": graph,
                "changed_modules": tuple(
                    sorted(changed_modules)
                ),
                "changed_symbols": tuple(
                    sorted(changed_symbols)
                ),
                "impacted_modules": tuple(
                    module_impacts
                ),
                "impacted_symbols": tuple(
                    symbol_impacts
                ),
                "impacted_calls": tuple(
                    call_impacts
                ),
                "direct_impact_count": direct_count,
                "transitive_impact_count": transitive_count,
                "impact_score": impact_score,
            }

            completed_at = datetime.now(timezone.utc)

            diagnostics.append(
                AnalysisDiagnostic(
                    message=(
                        "Change-impact analysis completed "
                        "successfully."
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
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Change-impact analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "change_impact_analysis",
            result,
        )

        return result
