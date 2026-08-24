from __future__ import annotations

from analyzer.call.builder import collect_call_relationships
from analyzer.call.models import CallGraph
from analyzer.call.resolver import resolve_call_relationships
from analyzer.core.repository_context import RepositoryContext
from analyzer.dependency.builder import build_dependency_graph
from analyzer.symbol.builder import build_symbol_graph
from analyzer.symbol.resolver import resolve_symbol_references


def ensure_taint_graphs(
    repository: RepositoryContext,
):
    """
    Ensure taint analysis has the repository graphs it requires.

    Taint analysis must not depend on analyzer execution order.
    """

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

        symbol_graph = resolve_symbol_references(
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

        call_graph = resolve_call_relationships(
            call_graph,
            symbol_graph,
            dependency_graph,
            source_by_file,
        )

        repository.set_artifact(
            "call_graph",
            call_graph,
        )

    return (
        dependency_graph,
        symbol_graph,
        call_graph,
    )
