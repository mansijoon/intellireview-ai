from __future__ import annotations

import ast
from pathlib import Path

from analyzer.core.repository_context import RepositoryContext
from analyzer.dependency.models import (
    DependencyGraph,
    ModuleNode,
)


def _module_name_from_path(
    repository_root: Path,
    file_path: Path,
) -> str:
    """
    Convert a Python file path into its module name.

    Examples:
        app.py                  -> app
        analyzer/code.py       -> analyzer.code
        package/__init__.py    -> package
    """

    relative = file_path.relative_to(
        repository_root
    )

    parts = list(
        relative.with_suffix("").parts
    )

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _module_name_from_relative_path(
    relative_path: str,
) -> str:
    """
    Convert a repository-relative Python path into a module name.
    """

    parts = list(
        Path(relative_path)
        .with_suffix("")
        .parts
    )

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _resolve_relative_import(
    current_module: str,
    level: int,
    module: str | None,
) -> str:
    """
    Resolve a Python relative import.
    """

    current_parts = current_module.split(".")

    if level > len(current_parts):
        return module or ""

    base = current_parts[:-level]

    if module:
        base.extend(
            module.split(".")
        )

    return ".".join(base)


def _find_internal_module(
    import_name: str,
    graph: DependencyGraph,
) -> str | None:
    """
    Resolve an import against modules known to the repository.

    Tries progressively shorter module names.
    """

    candidate = import_name

    while candidate:

        if candidate in graph:
            return candidate

        if "." not in candidate:
            break

        candidate = candidate.rsplit(
            ".",
            1,
        )[0]

    return None


def _add_internal_dependency(
    graph: DependencyGraph,
    source_module: ModuleNode,
    target_module_name: str,
) -> None:
    """
    Add an internal dependency and its reverse edge.
    """

    source_module.imports.add(
        target_module_name
    )

    target_module = graph.get_module(
        target_module_name
    )

    if target_module is not None:
        target_module.imported_by.add(
            source_module.name
        )


def _process_import(
    node: ast.Import,
    module: ModuleNode,
    graph: DependencyGraph,
) -> None:
    for alias in node.names:

        imported = alias.name

        resolved = _find_internal_module(
            imported,
            graph,
        )

        if resolved:
            _add_internal_dependency(
                graph,
                module,
                resolved,
            )
        else:
            module.external_imports.add(
                imported
            )


def _process_import_from(
    node: ast.ImportFrom,
    module: ModuleNode,
    graph: DependencyGraph,
) -> None:
    if node.level > 0:
        imported = _resolve_relative_import(
            module.name,
            node.level,
            node.module,
        )
    else:
        imported = node.module or ""

    resolved = _find_internal_module(
        imported,
        graph,
    )

    if not resolved:

        for alias in node.names:

            candidate = (
                f"{imported}.{alias.name}"
                if imported
                else alias.name
            )

            resolved = _find_internal_module(
                candidate,
                graph,
            )

            if resolved:
                break

    if resolved:

        _add_internal_dependency(
            graph,
            module,
            resolved,
        )

    elif imported:

        module.external_imports.add(
            imported
        )


def build_dependency_graph(
    repository: RepositoryContext,
) -> DependencyGraph:
    """
    Build a dependency graph from a RepositoryContext.

    The repository context owns file discovery and source/AST caching.
    This function only performs dependency inference.
    """

    graph = DependencyGraph()

    #
    # PASS 1
    # Register every Python module.
    #

    for source_file in repository.files:

        if source_file.language.lower() not in {
            "python",
            "py",
        }:
            continue

        module_name = _module_name_from_relative_path(
            source_file.path
        )

        if not module_name:
            continue

        graph.add_module(
            ModuleNode(
                name=module_name,
                path=source_file.path,
            )
        )

    #
    # PASS 2
    # Reuse the AnalysisContext AST.
    #

    for module in graph.modules.values():

        try:
            context = repository.get_context(
                module.path
            )
        except (KeyError, RuntimeError):
            continue

        tree = context.ast_tree

        if tree is None:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                _process_import(
                    node,
                    module,
                    graph,
                )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):

                _process_import_from(
                    node,
                    module,
                    graph,
                )

    return graph


def build_dependency_graph_from_path(
    repository_path: str,
) -> DependencyGraph:
    """
    Backward-compatible path-based entry point.

    New code should use RepositoryContext directly.
    """

    from analyzer.core.repository_loader import (
        RepositoryLoader,
    )

    repository = RepositoryLoader().load(
        repository_path
    )

    return build_dependency_graph(
        repository
    )
