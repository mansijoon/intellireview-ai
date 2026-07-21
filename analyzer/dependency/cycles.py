from analyzer.dependency.models import DependencyGraph


def find_dependency_cycles(graph: DependencyGraph):
    """
    Detect circular dependencies in the repository dependency graph.
    """

    visited = set()
    recursion_stack = []
    recursion_set = set()
    cycles = []

    def dfs(module_name):
        visited.add(module_name)
        recursion_stack.append(module_name)
        recursion_set.add(module_name)

        module = graph.modules[module_name]

        for dependency in module.imports:

            if dependency not in graph.modules:
                continue

            if dependency not in visited:
                dfs(dependency)

            elif dependency in recursion_set:
                start = recursion_stack.index(dependency)
                cycle = recursion_stack[start:] + [dependency]

                if cycle not in cycles:
                    cycles.append(cycle)

        recursion_stack.pop()
        recursion_set.remove(module_name)

    for module_name in graph.modules:
        if module_name not in visited:
            dfs(module_name)

    return cycles
