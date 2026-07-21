from analyzer.dependency.models import DependencyGraph


def get_internal_dependency_count(graph: DependencyGraph) -> int:
    """
    Total number of internal dependencies.
    """
    return sum(len(module.imports) for module in graph.modules.values())


def get_external_dependency_count(graph: DependencyGraph) -> int:
    """
    Total number of external dependencies.
    """
    return sum(len(module.external_imports) for module in graph.modules.values())


def get_most_depended_modules(graph: DependencyGraph, top_n: int = 10):
    """
    Modules that are imported by the largest number of other modules.
    """
    return sorted(
        graph.modules.values(),
        key=lambda module: len(module.imported_by),
        reverse=True
    )[:top_n]


def get_most_dependent_modules(graph: DependencyGraph, top_n: int = 10):
    """
    Modules having the highest number of outgoing dependencies.
    """
    return sorted(
        graph.modules.values(),
        key=lambda module: len(module.imports),
        reverse=True
    )[:top_n]
