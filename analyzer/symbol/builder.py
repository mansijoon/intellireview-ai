from __future__ import annotations

import ast
from pathlib import Path

from analyzer.core.models import SourceLocation
from analyzer.core.repository_context import RepositoryContext
from analyzer.symbol.models import SymbolGraph, SymbolNode
from analyzer.symbol.references import collect_symbol_references


def _module_name_from_path(
    relative_path: str,
) -> str:
    path = Path(relative_path)

    parts = list(
        path.with_suffix("").parts
    )

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


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

    end_column = getattr(
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
            end_column + 1
            if end_column is not None
            else None
        ),
    )


def _symbol_id(
    module_name: str,
    qualified_name: str,
) -> str:
    if not qualified_name:
        return module_name

    return f"{module_name}:{qualified_name}"


def _function_kind(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parent: SymbolNode | None,
) -> str:
    if parent is not None and parent.kind == "class":
        return "method"

    return "function"


def build_symbol_graph(
    repository: RepositoryContext,
) -> SymbolGraph:
    """Build a Python symbol graph using cached AnalysisContext ASTs."""

    graph = SymbolGraph()

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

        module_name = _module_name_from_path(
            source_file.path
        )

        module_symbol_id = _symbol_id(
            module_name,
            "",
        )

        module_symbol = SymbolNode(
            symbol_id=module_symbol_id,
            name=module_name,
            kind="module",
            module=module_name,
            location=SourceLocation(
                file_path=source_file.path,
                line_start=1,
                line_end=max(
                    1,
                    context.line_count,
                ),
            ),
        )

        graph.add_symbol(
            module_symbol
        )

        def visit_body(
            body: list[ast.stmt],
            parent: SymbolNode,
            qualified_prefix: str,
        ) -> None:
            for node in body:
                if isinstance(node, ast.ClassDef):
                    qualified_name = (
                        f"{qualified_prefix}.{node.name}"
                        if qualified_prefix
                        else node.name
                    )

                    symbol = SymbolNode(
                        symbol_id=_symbol_id(
                            module_name,
                            qualified_name,
                        ),
                        name=node.name,
                        kind="class",
                        module=module_name,
                        location=_location(
                            source_file.path,
                            node,
                        ),
                        parent_id=parent.symbol_id,
                    )

                    graph.add_symbol(symbol)

                    visit_body(
                        node.body,
                        symbol,
                        qualified_name,
                    )

                elif isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    qualified_name = (
                        f"{qualified_prefix}.{node.name}"
                        if qualified_prefix
                        else node.name
                    )

                    symbol = SymbolNode(
                        symbol_id=_symbol_id(
                            module_name,
                            qualified_name,
                        ),
                        name=node.name,
                        kind=_function_kind(
                            node,
                            parent,
                        ),
                        module=module_name,
                        location=_location(
                            source_file.path,
                            node,
                        ),
                        parent_id=parent.symbol_id,
                    )

                    graph.add_symbol(symbol)

                    visit_body(
                        node.body,
                        symbol,
                        qualified_name,
                    )

        visit_body(
            tree.body,
            module_symbol,
            "",
        )

        # Definitions must exist before references are collected,
        # because references need their containing source symbol.
        collect_symbol_references(
            graph,
            source_file.path,
            tree,
        )

    return graph
