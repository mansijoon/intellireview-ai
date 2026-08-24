from __future__ import annotations

from collections import deque

from analyzer.call.models import CallGraph
from analyzer.dependency.models import DependencyGraph
from analyzer.symbol.models import SymbolGraph

from analyzer.impact.models import (
    ImpactDepth,
    ImpactTarget,
    ImpactType,
)


def reverse_dependency_impact(
    graph: DependencyGraph,
    changed_modules: set[str],
) -> list[ImpactTarget]:
    """Find modules that directly or transitively depend on changed modules."""

    impacted: list[ImpactTarget] = []
    visited: set[str] = set(changed_modules)

    queue: deque[tuple[str, ImpactDepth]] = deque(
        (module, ImpactDepth.DIRECT)
        for module in sorted(changed_modules)
    )

    while queue:
        target_module, depth = queue.popleft()

        node = graph.get_module(target_module)

        if node is None:
            continue

        for dependent in sorted(node.imported_by):
            if dependent in visited:
                continue

            visited.add(dependent)

            impacted.append(
                ImpactTarget(
                    target_id=dependent,
                    impact_type=ImpactType.MODULE,
                    depth=depth,
                    source_id=target_module,
                    reason=(
                        "Imports changed module."
                        if depth == ImpactDepth.DIRECT
                        else
                        "Transitively depends on changed module."
                    ),
                )
            )

            queue.append(
                (
                    dependent,
                    ImpactDepth.TRANSITIVE,
                )
            )

    return impacted


def reverse_symbol_impact(
    graph: SymbolGraph,
    changed_symbols: set[str],
) -> list[ImpactTarget]:
    """Find symbols referencing changed symbols."""

    impacted: list[ImpactTarget] = []

    direct_targets = {
        reference.source_symbol_id
        for reference in graph.references
        if (
            reference.target_symbol_id in changed_symbols
            and reference.source_symbol_id
            not in changed_symbols
        )
    }

    for symbol_id in sorted(direct_targets):
        symbol = graph.get_symbol(symbol_id)

        if symbol is None:
            continue

        impacted.append(
            ImpactTarget(
                target_id=symbol_id,
                impact_type=ImpactType.SYMBOL,
                depth=ImpactDepth.DIRECT,
                location=symbol.location,
                source_id=next(
                    (
                        reference.target_symbol_id
                        for reference in graph.references
                        if (
                            reference.source_symbol_id
                            == symbol_id
                            and reference.target_symbol_id
                            in changed_symbols
                        )
                    ),
                    None,
                ),
                reason="References changed symbol.",
            )
        )

    # Traverse symbol-reference edges transitively.
    visited = set(changed_symbols)
    visited.update(direct_targets)

    queue: deque[str] = deque(
        sorted(direct_targets)
    )

    while queue:
        source_symbol = queue.popleft()

        downstream = sorted(
            reference.source_symbol_id
            for reference in graph.references
            if (
                reference.target_symbol_id
                == source_symbol
                and reference.source_symbol_id
                not in visited
            )
        )

        for dependent in downstream:
            visited.add(dependent)

            symbol = graph.get_symbol(dependent)

            if symbol is None:
                continue

            impacted.append(
                ImpactTarget(
                    target_id=dependent,
                    impact_type=ImpactType.SYMBOL,
                    depth=ImpactDepth.TRANSITIVE,
                    location=symbol.location,
                    source_id=source_symbol,
                    reason=(
                        "Transitively references "
                        "changed symbol."
                    ),
                )
            )

            queue.append(dependent)

    return impacted


def reverse_call_impact(
    graph: CallGraph,
    changed_symbols: set[str],
) -> list[ImpactTarget]:
    """Find callers of changed symbols through the call graph."""

    impacted: list[ImpactTarget] = []

    direct_callers = {
        call.caller_symbol_id
        for call in graph.calls
        if (
            call.callee_symbol_id in changed_symbols
            and call.caller_symbol_id not in changed_symbols
        )
    }

    for caller_id in sorted(direct_callers):
        matching_call = next(
            (
                call
                for call in graph.calls
                if (
                    call.caller_symbol_id == caller_id
                    and call.callee_symbol_id
                    in changed_symbols
                )
            ),
            None,
        )

        impacted.append(
            ImpactTarget(
                target_id=caller_id,
                impact_type=ImpactType.CALL,
                depth=ImpactDepth.DIRECT,
                location=(
                    matching_call.location
                    if matching_call is not None
                    else None
                ),
                source_id=(
                    matching_call.callee_symbol_id
                    if matching_call is not None
                    else None
                ),
                reason="Calls changed symbol.",
            )
        )

    visited = set(changed_symbols)
    visited.update(direct_callers)

    queue: deque[str] = deque(
        sorted(direct_callers)
    )

    while queue:
        changed_caller = queue.popleft()

        upstream_callers = sorted(
            call.caller_symbol_id
            for call in graph.calls
            if (
                call.callee_symbol_id == changed_caller
                and call.caller_symbol_id not in visited
            )
        )

        for caller_id in upstream_callers:
            visited.add(caller_id)

            matching_call = next(
                (
                    call
                    for call in graph.calls
                    if (
                        call.caller_symbol_id == caller_id
                        and call.callee_symbol_id
                        == changed_caller
                    )
                ),
                None,
            )

            impacted.append(
                ImpactTarget(
                    target_id=caller_id,
                    impact_type=ImpactType.CALL,
                    depth=ImpactDepth.TRANSITIVE,
                    location=(
                        matching_call.location
                        if matching_call is not None
                        else None
                    ),
                    source_id=changed_caller,
                    reason=(
                        "Transitively calls changed symbol."
                    ),
                )
            )

            queue.append(caller_id)

    return impacted
