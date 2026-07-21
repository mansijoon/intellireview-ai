from analyzer.dependency.builder import build_dependency_graph
from analyzer.dependency.graph import (
    get_internal_dependency_count,
    get_external_dependency_count,
    get_most_depended_modules,
    get_most_dependent_modules,
)
from analyzer.dependency.visualizer import (
    build_dependency_visualization,
)
from analyzer.dependency.cycles import (
    find_dependency_cycles,
)


def analyze_repository_dependencies(repo_path):
    """
    Analyze repository dependencies and prepare
    data for UI, PDF and AI modules.
    """

    graph = build_dependency_graph(repo_path)

    visualization = build_dependency_visualization(
        graph
    )
    
    cycles = find_dependency_cycles(
        graph
    )
    
    

    return {
        "graph": graph,
        "visualization": visualization,
        "cycles": cycles,
        "total_modules": len(graph),
        "internal_dependencies": get_internal_dependency_count(graph),
        "external_dependencies": get_external_dependency_count(graph),
        "most_depended_modules": get_most_depended_modules(graph),
        "most_dependent_modules": get_most_dependent_modules(graph),
    }
