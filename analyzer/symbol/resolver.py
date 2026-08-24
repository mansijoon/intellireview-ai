from __future__ import annotations

from analyzer.dependency.models import DependencyGraph
from analyzer.symbol.models import (
    SymbolGraph,
    SymbolNode,
    SymbolReference,
    SymbolResolutionStatus,
)


def _module_symbols(
    graph: SymbolGraph,
    module: str,
) -> tuple[SymbolNode, ...]:
    return tuple(
        symbol
        for symbol in graph.symbols.values()
        if symbol.module == module
    )


def _find_by_qualified_name(
    graph: SymbolGraph,
    module: str,
    qualified_name: str,
) -> SymbolNode | None:
    return graph.get_symbol(
        f"{module}:{qualified_name}"
    )


def _find_by_name(
    graph: SymbolGraph,
    module: str,
    name: str,
) -> SymbolNode | None:
    candidates = tuple(
        symbol
        for symbol in _module_symbols(
            graph,
            module,
        )
        if symbol.name == name
    )

    if len(candidates) != 1:
        return None

    return candidates[0]


def _find_child(
    graph: SymbolGraph,
    parent: SymbolNode,
    name: str,
) -> SymbolNode | None:
    candidates = tuple(
        symbol
        for symbol in graph.symbols.values()
        if (
            symbol.parent_id == parent.symbol_id
            and symbol.name == name
        )
    )

    if len(candidates) != 1:
        return None

    return candidates[0]


def _resolve_qualified_local(
    graph: SymbolGraph,
    source_symbol: SymbolNode,
    referenced_name: str,
) -> SymbolNode | None:
    """
    Resolve references defined in the source module.

    Supports:
        calculate
        Calculator
        Calculator.run
    """

    direct = _find_by_qualified_name(
        graph,
        source_symbol.module,
        referenced_name,
    )

    if direct is not None:
        return direct

    parts = referenced_name.split(".")

    if not parts:
        return None

    current = _find_by_name(
        graph,
        source_symbol.module,
        parts[0],
    )

    if current is None:
        return None

    for part in parts[1:]:
        current = _find_child(
            graph,
            current,
            part,
        )

        if current is None:
            return None

    return current


def _resolve_dependency_symbol(
    graph: SymbolGraph,
    dependency_graph: DependencyGraph,
    source_symbol: SymbolNode,
    referenced_name: str,
) -> SymbolNode | None:
    """
    Resolve a reference against modules imported by the
    source module.

    This intentionally resolves only statically provable
    module-qualified or imported symbols.
    """

    module_node = dependency_graph.get_module(
        source_symbol.module
    )

    if module_node is None:
        return None

    parts = referenced_name.split(".")

    if not parts:
        return None

    for dependency_module in sorted(
        module_node.imports
    ):
        # Direct imported symbol:
        #
        # from service import Calculator
        # Calculator -> service:Calculator
        target = _find_by_name(
            graph,
            dependency_module,
            parts[0],
        )

        if target is None:
            continue

        if len(parts) == 1:
            return target

        # Resolve children:
        #
        # Calculator.run
        # -> service:Calculator.run
        current = target

        for part in parts[1:]:
            current = _find_child(
                graph,
                current,
                part,
            )

            if current is None:
                break

        else:
            return current

    return None


def resolve_symbol_references(
    graph: SymbolGraph,
    dependency_graph: DependencyGraph,
) -> SymbolGraph:
    """
    Resolve collected symbol references conservatively.

    Resolution order:

        1. Same-module symbol
        2. Symbol exported by an internal dependency
        3. unresolved

    Ambiguous references are never guessed.
    """

    resolved: list[SymbolReference] = []

    for reference in graph.references:

        source_symbol = graph.get_symbol(
            reference.source_symbol_id
        )

        if source_symbol is None:
            resolved.append(reference)
            continue

        target = _resolve_qualified_local(
            graph,
            source_symbol,
            reference.referenced_name,
        )

        if target is None:
            target = _resolve_dependency_symbol(
                graph,
                dependency_graph,
                source_symbol,
                reference.referenced_name,
            )

        if target is None:
            resolved.append(
                SymbolReference(
                    source_symbol_id=(
                        reference.source_symbol_id
                    ),
                    referenced_name=(
                        reference.referenced_name
                    ),
                    location=reference.location,
                    target_symbol_id=None,
                    resolution_status=(
                        SymbolResolutionStatus.UNRESOLVED
                    ),
                )
            )
            continue

        resolved.append(
            SymbolReference(
                source_symbol_id=(
                    reference.source_symbol_id
                ),
                referenced_name=(
                    reference.referenced_name
                ),
                location=reference.location,
                target_symbol_id=target.symbol_id,
                resolution_status=(
                    SymbolResolutionStatus.RESOLVED
                ),
            )
        )

    graph.references = resolved

    return graph


def _resolve_constructor_target(
    graph: SymbolGraph,
    dependency_graph: DependencyGraph,
    source_symbol: SymbolNode,
    constructor_name: str,
) -> SymbolNode | None:
    """Resolve a constructor name to a repository class symbol."""

    target = _resolve_qualified_local(
        graph,
        source_symbol,
        constructor_name,
    )

    if target is not None and target.kind == "class":
        return target

    target = _resolve_dependency_symbol(
        graph,
        dependency_graph,
        source_symbol,
        constructor_name,
    )

    if target is not None and target.kind == "class":
        return target

    return None
