from __future__ import annotations

import ast

from analyzer.core.models import SourceLocation
from analyzer.symbol.models import SymbolGraph, SymbolNode, SymbolReference


def _location(
    file_path: str,
    node: ast.AST,
) -> SourceLocation:
    line_start = max(
        1,
        getattr(node, "lineno", 1),
    )

    line_end = getattr(
        node,
        "end_lineno",
        line_start,
    )

    column_start = getattr(
        node,
        "col_offset",
        None,
    )

    column_end = getattr(
        node,
        "end_col_offset",
        None,
    )

    return SourceLocation(
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        column_start=(
            column_start + 1
            if column_start is not None
            else None
        ),
        column_end=(
            column_end + 1
            if column_end is not None
            else None
        ),
    )


def _qualified_attribute(node: ast.Attribute) -> str:
    parts: list[str] = []
    current: ast.AST = node

    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        parts.append(current.id)
    else:
        parts.append("<expression>")

    return ".".join(reversed(parts))


def _containing_symbol(
    graph: SymbolGraph,
    file_path: str,
    line: int,
) -> SymbolNode | None:
    candidates = [
        symbol
        for symbol in graph.symbols.values()
        if (
            symbol.location.file_path == file_path
            and symbol.location.line_start <= line
            and (
                symbol.location.line_end is None
                or line <= symbol.location.line_end
            )
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda symbol: (
            symbol.location.line_start,
            symbol.location.line_end or symbol.location.line_start,
        ),
    )


def collect_symbol_references(
    graph: SymbolGraph,
    file_path: str,
    tree: ast.AST,
) -> None:
    """Collect statically observed Python symbol references."""

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            containing = _containing_symbol(
                graph,
                file_path,
                getattr(node, "lineno", 1),
            )

            if containing is None:
                continue

            graph.add_reference(
                SymbolReference(
                    source_symbol_id=containing.symbol_id,
                    referenced_name=node.id,
                    location=_location(
                        file_path,
                        node,
                    ),
                )
            )

        elif isinstance(node, ast.Attribute):
            containing = _containing_symbol(
                graph,
                file_path,
                getattr(node, "lineno", 1),
            )

            if containing is None:
                continue

            graph.add_reference(
                SymbolReference(
                    source_symbol_id=containing.symbol_id,
                    referenced_name=_qualified_attribute(node),
                    location=_location(
                        file_path,
                        node,
                    ),
                )
            )
