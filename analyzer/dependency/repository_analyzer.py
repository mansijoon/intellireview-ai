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
from analyzer.dependency.cycles import find_dependency_cycles
from analyzer.dependency.graph import (
    get_external_dependency_count,
    get_internal_dependency_count,
    get_most_depended_modules,
    get_most_dependent_modules,
)


class DependencyRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide dependency analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="dependency",
        name="Dependency Analyzer",
        description=(
            "Builds the repository dependency graph and "
            "detects dependency relationships and cycles."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            graph = build_dependency_graph(
                repository
            )

            cycles = find_dependency_cycles(
                graph
            )

            internal_count = (
                get_internal_dependency_count(
                    graph
                )
            )

            external_count = (
                get_external_dependency_count(
                    graph
                )
            )

            most_depended = (
                get_most_depended_modules(
                    graph
                )
            )

            most_dependent = (
                get_most_dependent_modules(
                    graph
                )
            )

            artifacts = {
                "dependency_graph": graph,
                "dependency_cycles": cycles,
                "internal_dependency_count": (
                    internal_count
                ),
                "external_dependency_count": (
                    external_count
                ),
                "most_depended_modules": (
                    most_depended
                ),
                "most_dependent_modules": (
                    most_dependent
                ),
            }

            repository.set_artifact(
                "dependency_analysis",
                None,
            )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="dependency",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dependency analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "dependency_analysis",
                result,
            )

            return result

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="dependency",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Dependency analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "dependency_analysis",
                result,
            )

            return result
