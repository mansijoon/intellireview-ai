from __future__ import annotations

from datetime import datetime, timezone

from analyzer.architecture.models import (
    ArchitectureViolation,
)
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
from analyzer.impact.models import ChangeImpactGraph
from analyzer.symbol.builder import build_symbol_graph
from analyzer.symbol.resolver import resolve_symbol_references

from analyzer.risk.scoring import calculate_repository_risk


class RepositoryRiskRepositoryAnalyzer(
    RepositoryAnalyzer
):
    """Repository-wide structural risk analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="repository_risk",
            depends_on=frozenset({"dependency", "symbol", "call", "architecture", "change_impact"}),
        source_sensitive=False,
        name="Repository Risk Analyzer",
        description=(
            "Calculates repository and module risk from "
            "dependency, architecture, symbol, call, and "
            "change-impact intelligence."
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

            call_graph = repository.get_artifact(
                "call_graph"
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

                    partial = collect_call_relationships(
                        symbol_graph,
                        source_file.path,
                        tree,
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

            architecture_result = (
                repository.get_artifact(
                    "architecture_validation_analysis"
                )
            )

            architecture_violations: tuple[
                ArchitectureViolation, ...
            ] = ()

            if architecture_result is not None:
                architecture_violations = tuple(
                    architecture_result.artifacts.get(
                        "architecture_violations",
                        (),
                    )
                )

            impact_result = repository.get_artifact(
                "change_impact_analysis"
            )

            impact_graph: ChangeImpactGraph | None = None

            if impact_result is not None:
                impact_graph = impact_result.artifacts.get(
                    "impact_graph"
                )

            report = calculate_repository_risk(
                dependency_graph=dependency_graph,
                symbol_graph=symbol_graph,
                call_graph=call_graph,
                architecture_violations=(
                    architecture_violations
                ),
                impact_graph=impact_graph,
            )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "risk_report": report,
                    "repository_risk_score": (
                        report.risk_score
                    ),
                    "repository_risk_level": (
                        report.risk_level
                    ),
                    "risk_factors": tuple(
                        report.factors
                    ),
                    "module_risks": tuple(
                        report.module_risks
                    ),
                    "high_risk_modules": (
                        report.high_risk_modules
                    ),
                },
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Repository risk analysis "
                            "completed successfully."
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
                            "Repository risk analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "repository_risk_analysis",
            result,
        )

        return result
