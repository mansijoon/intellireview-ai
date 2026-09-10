from analyzer.core.cache.invalidation import DependencyInvalidator
from analyzer.dependency.models import DependencyGraph, ModuleNode


def test_dependency_invalidator_propagates_to_dependents():
    graph = DependencyGraph()

    a = ModuleNode(
        name="a",
        path="a.py",
        imported_by={"b"},
    )

    b = ModuleNode(
        name="b",
        path="b.py",
        imports={"a"},
    )

    c = ModuleNode(
        name="c",
        path="c.py",
    )

    graph.add_module(a)
    graph.add_module(b)
    graph.add_module(c)

    affected = DependencyInvalidator().affected_modules(
        graph,
        {"a.py"},
    )

    assert affected == frozenset({
        "a",
        "b",
    })

    assert "c" not in affected
