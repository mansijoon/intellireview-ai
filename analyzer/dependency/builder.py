import ast
from pathlib import Path

from analyzer.dependency.models import (
    DependencyGraph,
    ModuleNode,
)


def _module_name_from_path(repository: Path, file_path: Path):
    """
    Convert a Python file path into its module name.

    Examples:
        app.py                    -> app
        analyzer/code.py          -> analyzer.code
        flask/json/provider.py    -> flask.json.provider
        flask/__init__.py         -> flask
    """

    relative = file_path.relative_to(repository)

    parts = list(relative.with_suffix("").parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def _resolve_relative_import(current_module, level, module):
    """
    Resolve relative imports.

    Example:

        current = flask.json.provider

        from .tag import X
            -> flask.json.tag

        from ..ctx import Y
            -> flask.ctx

        from . import helpers
            -> flask.json
    """

    current_parts = current_module.split(".")

    if level > len(current_parts):
        return module or ""

    base = current_parts[:-level]

    if module:
        base.extend(module.split("."))

    return ".".join(base)


def _find_internal_module(import_name, graph):
    """
    Attempt to resolve an imported module against the repository.

    Tries progressively shorter package names.

    Example:

        flask.json.provider.DefaultJSONProvider
            -> flask.json.provider
            -> flask.json
            -> flask
    """

    candidate = import_name

    while candidate:

        if candidate in graph:
            return candidate

        if "." not in candidate:
            break

        candidate = candidate.rsplit(".", 1)[0]

    return None


def build_dependency_graph(repository_path: str):

    repository = Path(repository_path)

    graph = DependencyGraph()

    #
    # PASS 1
    # Register every Python module
    #

    for file_path in repository.rglob("*.py"):

        module_name = _module_name_from_path(
            repository,
            file_path
        )

        graph.add_module(
            ModuleNode(
                name=module_name,
                path=str(file_path.relative_to(repository))
            )
        )

    #
    # PASS 2
    # Parse imports
    #

    for module in graph.modules.values():

        file_path = repository / module.path

        try:

            source = file_path.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(source)

        except Exception:
            continue

        for node in ast.walk(tree):

            #
            # import x
            #

            if isinstance(node, ast.Import):

                for alias in node.names:

                    imported = alias.name

                    resolved = _find_internal_module(
                        imported,
                        graph
                    )

                    if resolved:

                        module.imports.add(resolved)

                        graph.get_module(
                            resolved
                        ).imported_by.add(
                            module.name
                        )

                    else:

                        module.external_imports.add(
                            imported
                        )

            #
            # from x import y
            #

            elif isinstance(node, ast.ImportFrom):

                #
                # Resolve relative imports
                #

                if node.level > 0:

                    imported = _resolve_relative_import(
                        module.name,
                        node.level,
                        node.module
                    )

                else:

                    imported = node.module or ""

                #
                # First try the imported package itself
                #

                resolved = _find_internal_module(
                    imported,
                    graph
                )

                #
                # Then try imported.symbol
                #

                if not resolved:

                    for alias in node.names:

                        candidate = (
                            f"{imported}.{alias.name}"
                            if imported
                            else alias.name
                        )

                        resolved = _find_internal_module(
                            candidate,
                            graph
                        )

                        if resolved:
                            break

                if resolved:

                    module.imports.add(resolved)

                    graph.get_module(
                        resolved
                    ).imported_by.add(
                        module.name
                    )

                else:

                    if imported:

                        module.external_imports.add(
                            imported
                        )

    return graph
