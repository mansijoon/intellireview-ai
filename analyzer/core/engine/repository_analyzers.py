from __future__ import annotations

from analyzer.core.repository_context import RepositoryContext
from analyzer.core.engine.repository_analyzer import (
    RepositoryAnalyzer,
)
from analyzer.dependency.builder import build_dependency_graph
from analyzer.dependency.cycles import find_dependency_cycles
from analyzer.dependency.graph import (
    get_external_dependency_count,
    get_internal_dependency_count,
    get_most_depended_modules,
    get_most_dependent_modules,
)


class DependencyRepositoryAnalyzer(RepositoryAnalyzer):
    """Build and register the repository dependency graph."""

    @property
    def analyzer_id(self) -> str:
        return "dependency"

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> dict:
        graph = build_dependency_graph(
            repository
        )

        cycles = find_dependency_cycles(
            graph
        )

        result = {
            "graph": graph,
            "cycles": cycles,
            "internal_count": (
                get_internal_dependency_count(
                    graph
                )
            ),
            "external_count": (
                get_external_dependency_count(
                    graph
                )
            ),
            "most_depended": (
                get_most_depended_modules(
                    graph
                )
            ),
            "most_dependent": (
                get_most_dependent_modules(
                    graph
                )
            ),
        }

        repository.set_artifact(
            "dependency_analysis",
            result,
        )

        repository.set_artifact(
            "dependency_graph",
            graph,
        )

        repository.set_artifact(
            "dependency_cycles",
            cycles,
        )

        return result
