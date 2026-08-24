from __future__ import annotations

from analyzer.core import RepositoryContext
from analyzer.dependency import DependencyRepositoryAnalyzer
from analyzer.dependency.visualizer import (
    build_dependency_visualization,
)


def _get_or_run_dependency_analysis(
    repository: RepositoryContext,
):
    """Return the canonical dependency-analysis result."""

    result = repository.get_artifact(
        "dependency_analysis"
    )

    if result is None:
        result = DependencyRepositoryAnalyzer().analyze(
            repository
        )

    return result


def analyze_repository_dependencies(
    repository: RepositoryContext,
):
    """
    Compatibility API for repository dependency analysis.

    The canonical implementation lives in
    DependencyRepositoryAnalyzer.
    """

    result = _get_or_run_dependency_analysis(
        repository
    )

    return {
        "result": result,
        "graph": result.artifacts.get(
            "dependency_graph"
        ),
        "cycles": result.artifacts.get(
            "dependency_cycles",
            [],
        ),
        "internal_count": result.artifacts.get(
            "internal_dependency_count",
            0,
        ),
        "external_count": result.artifacts.get(
            "external_dependency_count",
            0,
        ),
        "most_depended": result.artifacts.get(
            "most_depended_modules",
            [],
        ),
        "most_dependent": result.artifacts.get(
            "most_dependent_modules",
            [],
        ),
    }


def visualize_repository_dependencies(
    repository: RepositoryContext,
    output_path: str = "dependency_graph.html",
):
    """
    Generate dependency visualization from the canonical
    dependency-analysis artifact.
    """

    result = _get_or_run_dependency_analysis(
        repository
    )

    graph = result.artifacts.get(
        "dependency_graph"
    )

    if graph is None:
        raise RuntimeError(
            "Dependency graph artifact is unavailable."
        )

    network = build_dependency_visualization(
        graph
    )

    network.write_html(
        output_path
    )

    return output_path
