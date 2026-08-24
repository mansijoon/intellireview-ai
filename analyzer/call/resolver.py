from __future__ import annotations

import ast

from analyzer.dependency.models import DependencyGraph
from analyzer.symbol.models import SymbolGraph, SymbolNode
from analyzer.symbol.resolver import (
    _resolve_dependency_symbol,
    _resolve_qualified_local,
    _resolve_constructor_target,
)

from analyzer.call.models import (
    CallGraph,
    CallRelationship,
    CallResolutionStatus,
)


def _collect_local_bindings(
    source: str,
    caller: SymbolNode,
    symbol_graph: SymbolGraph,
    dependency_graph: DependencyGraph,
) -> dict[str, SymbolNode]:
    """
    Collect conservative local variable -> class bindings.

    Supported form:

        calculator = Calculator()

    The binding is accepted only when Calculator resolves
    to a repository class.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    bindings: dict[str, SymbolNode] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        if not isinstance(node.value, ast.Call):
            continue

        if not isinstance(node.value.func, (ast.Name, ast.Attribute)):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not isinstance(target, ast.Name):
            continue

        if isinstance(node.value.func, ast.Name):
            constructor_name = node.value.func.id
        else:
            constructor_name = ast.unparse(
                node.value.func
            )

        constructor = _resolve_qualified_local(
            symbol_graph,
            caller,
            constructor_name,
        )

        if constructor is None:
            constructor = _resolve_dependency_symbol(
                symbol_graph,
                dependency_graph,
                caller,
                constructor_name,
            )

        if constructor is None or constructor.kind != "class":
            continue

        bindings[target.id] = constructor

    return bindings


def _resolve_bound_method(
    symbol_graph: SymbolGraph,
    binding: SymbolNode,
    method_name: str,
) -> SymbolNode | None:
    candidates = tuple(
        symbol
        for symbol in symbol_graph.symbols.values()
        if (
            symbol.parent_id == binding.symbol_id
            and symbol.name == method_name
            and symbol.kind == "method"
        )
    )

    if len(candidates) != 1:
        return None

    return candidates[0]


def _resolve_call_target(
    call: CallRelationship,
    caller: SymbolNode,
    symbol_graph: SymbolGraph,
    dependency_graph: DependencyGraph,
    bindings: dict[str, SymbolNode],
) -> SymbolNode | None:
    """
    Resolve a call using conservative static resolution.

    Resolution order:

        1. Bound instance method
        2. Same-module symbol
        3. Internal dependency symbol
        4. unresolved
    """

    if "." in call.callee_name:
        base, method = call.callee_name.split(
            ".",
            1,
        )

        binding = bindings.get(base)

        if binding is not None:
            target = _resolve_bound_method(
                symbol_graph,
                binding,
                method,
            )

            if target is not None:
                return target

    target = _resolve_qualified_local(
        symbol_graph,
        caller,
        call.callee_name,
    )

    if target is not None:
        return target

    return _resolve_dependency_symbol(
        symbol_graph,
        dependency_graph,
        caller,
        call.callee_name,
    )


def resolve_call_relationships(
    call_graph: CallGraph,
    symbol_graph: SymbolGraph,
    dependency_graph: DependencyGraph,
    source_by_file: dict[str, str] | None = None,
) -> CallGraph:
    """
    Resolve call targets using repository symbols and conservative
    local constructor bindings.
    """

    resolved_calls: list[CallRelationship] = []

    bindings_by_caller: dict[str, dict[str, SymbolNode]] = {}

    for call in call_graph.calls:
        caller = symbol_graph.get_symbol(
            call.caller_symbol_id
        )

        if caller is None:
            resolved_calls.append(call)
            continue

        if caller.symbol_id not in bindings_by_caller:
            source = (
                source_by_file.get(
                    caller.location.file_path,
                    "",
                )
                if source_by_file is not None
                else ""
            )

            bindings_by_caller[
                caller.symbol_id
            ] = _collect_local_bindings(
                source,
                caller,
                symbol_graph,
                dependency_graph,
            )

        target = _resolve_call_target(
            call,
            caller,
            symbol_graph,
            dependency_graph,
            bindings_by_caller[
                caller.symbol_id
            ],
        )

        if target is None:
            resolved_calls.append(
                CallRelationship(
                    caller_symbol_id=call.caller_symbol_id,
                    callee_name=call.callee_name,
                    location=call.location,
                    callee_symbol_id=None,
                    resolution_status=(
                        CallResolutionStatus.UNRESOLVED
                    ),
                )
            )
            continue

        resolved_calls.append(
            CallRelationship(
                caller_symbol_id=call.caller_symbol_id,
                callee_name=call.callee_name,
                location=call.location,
                callee_symbol_id=target.symbol_id,
                resolution_status=(
                    CallResolutionStatus.RESOLVED
                ),
            )
        )

    call_graph.calls = resolved_calls

    return call_graph
