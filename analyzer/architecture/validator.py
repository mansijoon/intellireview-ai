from __future__ import annotations

from analyzer.architecture.models import (
    ArchitectureViolation,
    ArchitectureViolationType,
)
from analyzer.dependency.cycles import find_dependency_cycles
from analyzer.dependency.models import DependencyGraph


def validate_dependency_cycles(
    graph: DependencyGraph,
) -> list[ArchitectureViolation]:
    """Convert dependency cycles into architecture violations."""

    violations: list[ArchitectureViolation] = []

    for cycle in find_dependency_cycles(graph):
        path = " -> ".join(cycle)

        violations.append(
            ArchitectureViolation(
                violation_type=(
                    ArchitectureViolationType.DEPENDENCY_CYCLE
                ),
                severity="high",
                message=(
                    "Circular dependency detected: "
                    f"{path}"
                ),
                source_module=(
                    cycle[0] if cycle else None
                ),
                target_module=(
                    cycle[-1] if cycle else None
                ),
            )
        )

    return violations


def validate_forbidden_dependencies(
    graph: DependencyGraph,
    forbidden_dependencies: dict[str, set[str]] | None = None,
) -> list[ArchitectureViolation]:
    """
    Validate explicitly configured forbidden module dependencies.

    Mapping format:

        {
            "presentation": {"database", "storage"},
            "api": {"infrastructure"},
        }
    """

    if not forbidden_dependencies:
        return []

    violations: list[ArchitectureViolation] = []

    for source_module, forbidden_targets in (
        forbidden_dependencies.items()
    ):
        module = graph.get_module(source_module)

        if module is None:
            continue

        for target_module in sorted(
            module.imports & forbidden_targets
        ):
            violations.append(
                ArchitectureViolation(
                    violation_type=(
                        ArchitectureViolationType.FORBIDDEN_DEPENDENCY
                    ),
                    severity="high",
                    message=(
                        f"Module '{source_module}' depends on "
                        f"forbidden module '{target_module}'."
                    ),
                    source_module=source_module,
                    target_module=target_module,
                )
            )

    return violations


def validate_high_coupling(
    graph: DependencyGraph,
    threshold: int = 10,
) -> list[ArchitectureViolation]:
    """Flag modules with excessive total dependency coupling."""

    if threshold < 1:
        raise ValueError(
            "threshold must be >= 1"
        )

    violations: list[ArchitectureViolation] = []

    for module in graph.modules.values():
        coupling = (
            len(module.imports)
            + len(module.imported_by)
        )

        if coupling < threshold:
            continue

        violations.append(
            ArchitectureViolation(
                violation_type=(
                    ArchitectureViolationType.HIGH_COUPLING
                ),
                severity="medium",
                message=(
                    f"Module '{module.name}' has "
                    f"coupling of {coupling}, "
                    f"exceeding threshold {threshold}."
                ),
                source_module=module.name,
            )
        )

    return violations


def validate_architecture(
    graph: DependencyGraph,
    *,
    forbidden_dependencies: dict[str, set[str]] | None = None,
    coupling_threshold: int = 10,
) -> list[ArchitectureViolation]:
    """Run all deterministic architecture validation checks."""

    return (
        validate_dependency_cycles(graph)
        + validate_forbidden_dependencies(
            graph,
            forbidden_dependencies,
        )
        + validate_high_coupling(
            graph,
            coupling_threshold,
        )
    )
