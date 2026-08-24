from __future__ import annotations

import ast
from dataclasses import dataclass

from analyzer.core.context import AnalysisContext
from analyzer.core.models import Finding, SourceLocation
from analyzer.core.repository_context import RepositoryContext

from analyzer.taint.models import (
    TaintPath,
    TaintSink,
    TaintSource,
)


@dataclass(frozen=True, slots=True)
class TaintCallBinding:
    caller_symbol_id: str
    callee_symbol_id: str
    argument_name: str
    parameter_name: str
    location: SourceLocation


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


def _find_call(
    context: AnalysisContext,
    line: int,
) -> ast.Call | None:
    tree = context.ast_tree

    if tree is None:
        return None

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and getattr(node, "lineno", None) == line
        ):
            return node

    return None


def _find_function(
    context: AnalysisContext,
    name: str,
    line: int,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    tree = context.ast_tree

    if tree is None:
        return None

    candidates = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if node.name != name:
            continue

        candidates.append(node)

    if not candidates:
        return None

    # Prefer the function whose declaration is closest
    # to the resolved symbol location.
    return min(
        candidates,
        key=lambda node: abs(
            getattr(node, "lineno", 0) - line
        ),
    )


def _argument_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    return _qualified_name(node)


def _source_from_variable(
    variable: str,
    sources: dict[str, TaintSource],
) -> TaintSource | None:
    return sources.get(variable)


def _collect_local_sources(
    context: AnalysisContext,
) -> dict[str, TaintSource]:
    tree = context.ast_tree

    if tree is None:
        return {}

    sources: dict[str, TaintSource] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not isinstance(target, ast.Name):
            continue

        value = node.value

        if not isinstance(value, ast.Call):
            continue

        name = _qualified_name(value.func)

        if name not in {
            "input",
            "builtins.input",
            "request.get",
            "request.args.get",
            "request.form.get",
        }:
            continue

        sources[target.id] = TaintSource(
            source_id=(
                f"{context.file_path}:"
                f"{getattr(value, 'lineno', 1)}:"
                f"{name}"
            ),
            name=name,
            location=SourceLocation(
                file_path=context.file_path,
                line_start=getattr(
                    value,
                    "lineno",
                    1,
                ),
            ),
            kind="user_input",
        )

    return sources


def _sink_from_call(
    context: AnalysisContext,
    node: ast.Call,
) -> tuple[str, str] | None:
    name = _qualified_name(node.func)

    if name in {
        "subprocess.run",
        "subprocess.call",
        "subprocess.Popen",
        "os.system",
    }:
        return name, "shell_execution"

    if name in {
        "eval",
        "exec",
    }:
        return name, "dynamic_code_execution"

    if name in {
        "pickle.loads",
        "pickle.load",
        "yaml.load",
    }:
        return name, "unsafe_deserialization"

    return None


def _location(
    context: AnalysisContext,
    node: ast.AST,
) -> SourceLocation:
    return SourceLocation(
        file_path=context.file_path,
        line_start=getattr(
            node,
            "lineno",
            1,
        ),
        line_end=getattr(
            node,
            "end_lineno",
            getattr(node, "lineno", 1),
        ),
    )


def _parameter_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    arguments = function.args

    return [
        argument.arg
        for argument in (
            list(arguments.posonlyargs)
            + list(arguments.args)
            + list(arguments.kwonlyargs)
        )
    ]


def _find_sinks_for_parameter(
    context: AnalysisContext,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter: str,
    source: TaintSource,
) -> list[tuple[TaintSink, Finding]]:
    findings = []
    sinks = []

    tainted = {parameter}

    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            if isinstance(node.value, ast.Name):
                if node.value.id in tainted:
                    tainted.add(target.id)

        if not isinstance(node, ast.Call):
            continue

        sink_info = _sink_from_call(
            context,
            node,
        )

        if sink_info is None:
            continue

        sink_name, sink_kind = sink_info

        argument_is_tainted = any(
            isinstance(argument, ast.Name)
            and argument.id in tainted
            for argument in node.args
        )

        if not argument_is_tainted:
            continue

        sink = TaintSink(
            sink_id=(
                f"{context.file_path}:"
                f"{getattr(node, 'lineno', 1)}:"
                f"{sink_name}"
            ),
            name=sink_name,
            location=_location(
                context,
                node,
            ),
            kind=sink_kind,
        )

        severity = (
            "critical"
            if sink_kind in {
                "dynamic_code_execution",
                "unsafe_deserialization",
            }
            else "high"
        )

        finding = Finding(
            rule_id="SEC-TAINT-002",
            title=(
                "Tainted data crosses a function boundary "
                "and reaches a security-sensitive sink"
            ),
            description=(
                f"Tainted source '{source.name}' reaches "
                f"'{sink_name}' through parameter "
                f"'{parameter}'."
            ),
            severity=severity,
            location=sink.location,
            analyzer="taint",
            confidence=0.85,
            remediation=(
                "Validate or sanitize untrusted input before "
                "passing it across the function boundary."
            ),
        )

        sinks.append((sink, finding))

    return sinks


def analyze_interprocedural_taint(
    repository: RepositoryContext,
) -> tuple[
    list[TaintPath],
    list[Finding],
    list[TaintCallBinding],
]:
    symbol_graph = repository.get_artifact(
        "symbol_graph"
    )

    call_graph = repository.get_artifact(
        "call_graph"
    )

    if symbol_graph is None or call_graph is None:
        return [], [], []

    paths = []
    findings = []
    bindings = []

    for call in call_graph.calls:
        if call.callee_symbol_id is None:
            continue

        caller = symbol_graph.get_symbol(
            call.caller_symbol_id
        )

        callee = symbol_graph.get_symbol(
            call.callee_symbol_id
        )

        if caller is None or callee is None:
            continue

        caller_context = repository.get_context(
            caller.location.file_path
        )

        callee_context = repository.get_context(
            callee.location.file_path
        )

        call_node = _find_call(
            caller_context,
            call.location.line_start,
        )

        if call_node is None:
            continue

        sources = _collect_local_sources(
            caller_context
        )

        parameters_node = _find_function(
            callee_context,
            callee.name,
            callee.location.line_start,
        )

        if parameters_node is None:
            continue

        parameters = _parameter_names(
            parameters_node
        )

        for index, argument in enumerate(
            call_node.args
        ):
            if index >= len(parameters):
                continue

            argument_name = _argument_name(
                argument
            )

            if argument_name is None:
                continue

            source = _source_from_variable(
                argument_name,
                sources,
            )

            if source is None:
                continue

            parameter = parameters[index]

            bindings.append(
                TaintCallBinding(
                    caller_symbol_id=(
                        call.caller_symbol_id
                    ),
                    callee_symbol_id=(
                        call.callee_symbol_id
                    ),
                    argument_name=argument_name,
                    parameter_name=parameter,
                    location=call.location,
                )
            )

            sink_results = _find_sinks_for_parameter(
                callee_context,
                parameters_node,
                parameter,
                source,
            )

            for sink, finding in sink_results:
                paths.append(
                    TaintPath(
                        source=source,
                        sink=sink,
                        propagation=(
                            argument_name,
                            f"{callee.name}.{parameter}",
                        ),
                    )
                )

                findings.append(finding)

    return paths, findings, bindings
