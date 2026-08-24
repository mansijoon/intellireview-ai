from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext
from analyzer.core.models import Finding, SourceLocation

from analyzer.taint.models import (
    TaintPath,
    TaintReport,
    TaintSink,
    TaintSource,
)


def _location(
    context: AnalysisContext,
    node: ast.AST,
) -> SourceLocation:
    line_start = max(
        1,
        getattr(node, "lineno", 1),
    )

    line_end = getattr(
        node,
        "end_lineno",
        line_start,
    )

    column_start = getattr(
        node,
        "col_offset",
        None,
    )

    column_end = getattr(
        node,
        "end_col_offset",
        None,
    )

    return SourceLocation(
        file_path=context.file_path,
        line_start=line_start,
        line_end=line_end,
        column_start=(
            column_start + 1
            if column_start is not None
            else None
        ),
        column_end=(
            column_end + 1
            if column_end is not None
            else None
        ),
    )


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


def _attribute_chain(
    node: ast.AST,
) -> str | None:
    return _qualified_name(node)


def _is_request_source(
    node: ast.AST,
) -> bool:
    name = _attribute_chain(node)

    if name is None:
        return False

    return (
        name == "request.args"
        or name == "request.form"
        or name == "request.json"
    )


def _is_environment_source(
    node: ast.AST,
) -> bool:
    name = _attribute_chain(node)

    if name is None:
        return False

    return (
        name.startswith("os.environ.")
        or name in {
            "os.environ",
            "environ",
        }
    )


def _source_call_kind(
    node: ast.Call,
) -> str | None:
    name = _qualified_name(node.func)

    if name == "input":
        return "user_input"

    if name in {
        "os.getenv",
        "os.environ.get",
    }:
        return "environment"

    return None


def _sink_name(
    node: ast.Call,
) -> tuple[str, str] | None:
    name = _qualified_name(node.func)

    if name in {"eval", "exec"}:
        return name, "dynamic_code_execution"

    if name == "os.system":
        return name, "shell_execution"

    if name in {
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
    }:
        shell_true = any(
            keyword.arg == "shell"
            and isinstance(
                keyword.value,
                ast.Constant,
            )
            and keyword.value.value is True
            for keyword in node.keywords
        )

        if shell_true:
            return name, "shell_execution"

    if name in {
        "pickle.load",
        "pickle.loads",
        "cPickle.load",
        "cPickle.loads",
    }:
        return name, "unsafe_deserialization"

    return None


def _expression_is_tainted(
    node: ast.AST,
    tainted: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in tainted

    if _is_request_source(node):
        return True

    if _is_environment_source(node):
        return True

    if isinstance(node, ast.Call):
        return _source_call_kind(node) is not None

    for child in ast.iter_child_nodes(node):
        if _expression_is_tainted(
            child,
            tainted,
        ):
            return True

    return False


def analyze_taint(
    context: AnalysisContext,
) -> tuple[TaintReport, list[Finding]]:
    tree = context.ast_tree

    if tree is None:
        return (
            TaintReport(
                file_count=1,
                source_count=0,
                sink_count=0,
                finding_count=0,
                affected_file_count=0,
            ),
            [],
        )

    sources: list[TaintSource] = []
    sinks: list[TaintSink] = []
    paths: list[TaintPath] = []
    findings: list[Finding] = []

    tainted: set[str] = set()
    source_by_variable: dict[str, TaintSource] = {}

    def record_source(
        node: ast.AST,
        name: str,
        kind: str,
    ) -> TaintSource:
        source = TaintSource(
            source_id=(
                f"{context.file_path}:"
                f"{getattr(node, 'lineno', 1)}:"
                f"{name}"
            ),
            name=name,
            location=_location(
                context,
                node,
            ),
            kind=kind,
        )

        sources.append(source)

        return source

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            if not isinstance(target, ast.Name):
                continue

            source_kind = None
            source_name = None

            if isinstance(node.value, ast.Call):
                source_kind = _source_call_kind(
                    node.value
                )

                if source_kind is not None:
                    source_name = _qualified_name(
                        node.value.func
                    )

            elif _is_request_source(node.value):
                source_kind = "request_input"
                source_name = _qualified_name(
                    node.value
                )

            elif _is_environment_source(node.value):
                source_kind = "environment"
                source_name = _qualified_name(
                    node.value
                )

            if source_kind is not None:
                source = record_source(
                    node.value,
                    source_name or "source",
                    source_kind,
                )

                tainted.add(target.id)
                source_by_variable[target.id] = source
                continue

            if _expression_is_tainted(
                node.value,
                tainted,
            ):
                tainted.add(target.id)

                for name in ast.walk(node.value):
                    if (
                        isinstance(name, ast.Name)
                        and name.id in source_by_variable
                    ):
                        source_by_variable[
                            target.id
                        ] = source_by_variable[
                            name.id
                        ]
                        break

        elif isinstance(node, ast.AnnAssign):
            if not isinstance(
                node.target,
                ast.Name,
            ):
                continue

            if node.value is None:
                continue

            source_kind = None
            source_name = None

            if isinstance(node.value, ast.Call):
                source_kind = _source_call_kind(
                    node.value
                )

                if source_kind is not None:
                    source_name = _qualified_name(
                        node.value.func
                    )

            elif _is_request_source(node.value):
                source_kind = "request_input"
                source_name = _qualified_name(
                    node.value
                )

            elif _is_environment_source(node.value):
                source_kind = "environment"
                source_name = _qualified_name(
                    node.value
                )

            if source_kind is not None:
                source = record_source(
                    node.value,
                    source_name or "source",
                    source_kind,
                )

                tainted.add(node.target.id)
                source_by_variable[
                    node.target.id
                ] = source

        elif isinstance(node, ast.Call):
            sink = _sink_name(node)

            if sink is None:
                continue

            sink_name, sink_kind = sink

            sink_location = _location(
                context,
                node,
            )

            sink_model = TaintSink(
                sink_id=(
                    f"{context.file_path}:"
                    f"{getattr(node, 'lineno', 1)}:"
                    f"{sink_name}"
                ),
                name=sink_name,
                location=sink_location,
                kind=sink_kind,
            )

            sinks.append(sink_model)

            tainted_arguments = [
                argument
                for argument in node.args
                if _expression_is_tainted(
                    argument,
                    tainted,
                )
            ]

            if not tainted_arguments:
                continue

            source = None

            for argument in tainted_arguments:
                for name in ast.walk(argument):
                    if (
                        isinstance(name, ast.Name)
                        and name.id in source_by_variable
                    ):
                        source = source_by_variable[
                            name.id
                        ]
                        break

                if source is not None:
                    break

            if source is None:
                continue

            propagation = tuple(
                sorted(tainted)
            )

            path = TaintPath(
                source=source,
                sink=sink_model,
                propagation=propagation,
            )

            paths.append(path)

            findings.append(
                Finding(
                    rule_id="SEC-TAINT-001",
                    title="Tainted data reaches security-sensitive sink",
                    description=(
                        f"Tainted source '{source.name}' "
                        f"reaches '{sink_name}'."
                    ),
                    severity=(
                        "critical"
                        if sink_kind
                        in {
                            "dynamic_code_execution",
                            "unsafe_deserialization",
                        }
                        else "high"
                    ),
                    location=sink_location,
                    analyzer="taint",
                    confidence=0.90,
                    remediation=(
                        "Validate or sanitize the source data "
                        "before it reaches the security-sensitive "
                        "sink. Prefer APIs that do not interpret "
                        "input as code or shell commands."
                    ),
                )
            )

    affected = (
        1
        if findings
        else 0
    )

    report = TaintReport(
        file_count=1,
        source_count=len(sources),
        sink_count=len(sinks),
        finding_count=len(findings),
        affected_file_count=affected,
        paths=paths,
    )

    return report, findings
