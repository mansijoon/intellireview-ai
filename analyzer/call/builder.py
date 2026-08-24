from __future__ import annotations

import ast

from analyzer.core.models import SourceLocation
from analyzer.symbol.models import SymbolGraph, SymbolNode
from analyzer.call.models import (
    CallGraph,
    CallRelationship,
)


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


def _callee_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
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

    return "<expression>"


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
            -(
                symbol.location.line_end
                or symbol.location.line_start
            ),
        ),
    )


def collect_call_relationships(
    graph: SymbolGraph,
    file_path: str,
    tree: ast.AST,
) -> CallGraph:
    """Collect statically observed Python call expressions."""

    call_graph = CallGraph()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        caller = _containing_symbol(
            graph,
            file_path,
            getattr(node, "lineno", 1),
        )

        if caller is None:
            continue

        callee_name = _callee_name(node.func)

        call_graph.add_call(
            CallRelationship(
                caller_symbol_id=caller.symbol_id,
                callee_name=callee_name,
                location=_location(
                    file_path,
                    node,
                ),
            )
        )

    return call_graph
