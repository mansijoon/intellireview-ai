from __future__ import annotations

from analyzer.symbol.models import (
    SymbolGraph,
    SymbolNode,
)


def get_symbol_counts(
    graph: SymbolGraph,
) -> dict[str, int]:
    """Return counts grouped by symbol kind."""

    counts: dict[str, int] = {}

    for symbol in graph.symbols.values():
        counts[symbol.kind] = (
            counts.get(symbol.kind, 0) + 1
        )

    return counts


def get_symbols_by_module(
    graph: SymbolGraph,
    module: str,
) -> tuple[SymbolNode, ...]:
    return tuple(
        symbol
        for symbol in graph.symbols.values()
        if symbol.module == module
    )


def get_children(
    graph: SymbolGraph,
    symbol_id: str,
) -> tuple[SymbolNode, ...]:
    return tuple(
        symbol
        for symbol in graph.symbols.values()
        if symbol.parent_id == symbol_id
    )
