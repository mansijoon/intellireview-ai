from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)
from analyzer.core.rules import AnalysisRule, RuleMetadata


def _location(
    context: AnalysisContext,
    node: ast.AST,
) -> SourceLocation:
    line = max(1, getattr(node, "lineno", 1))
    end_line = max(
        line,
        getattr(node, "end_lineno", line),
    )

    column = getattr(node, "col_offset", None)

    return SourceLocation(
        file_path=context.file_path,
        line_start=line,
        line_end=end_line,
        column_start=(
            column + 1
            if column is not None
            else None
        ),
    )


def _finding(
    context: AnalysisContext,
    rule_id: str,
    title: str,
    description: str,
    node: ast.AST,
    severity: Severity,
    confidence: float,
    remediation: str,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=severity,
        location=_location(context, node),
        analyzer="performance",
        confidence=confidence,
        remediation=remediation,
    )


class NestedLoopRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PERF-PY-001",
        name="Nested Loop",
        description=(
            "Detects nested Python loops that may produce "
            "quadratic or worse runtime."
        ),
        category="performance",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings: list[Finding] = []

        for outer in ast.walk(tree):
            if not isinstance(
                outer,
                (ast.For, ast.AsyncFor, ast.While),
            ):
                continue

            for inner in ast.walk(outer):
                if inner is outer:
                    continue

                if not isinstance(
                    inner,
                    (ast.For, ast.AsyncFor, ast.While),
                ):
                    continue

                findings.append(
                    _finding(
                        context,
                        self.metadata.rule_id,
                        "Nested loop may increase runtime complexity",
                        (
                            "A loop contains another loop. If both loops "
                            "iterate over input-sized collections, this "
                            "may result in O(n²) or worse runtime."
                        ),
                        inner,
                        Severity.MEDIUM,
                        0.88,
                        (
                            "Check whether the nested iteration can be "
                            "replaced with indexing, hashing, precomputation, "
                            "or a more efficient algorithm."
                        ),
                    )
                )

                break

        return findings


class RepeatedMembershipRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PERF-PY-002",
        name="Repeated Linear Membership Check",
        description=(
            "Detects membership checks against list-like expressions "
            "inside loops."
        ),
        category="performance",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings: list[Finding] = []

        for loop in ast.walk(tree):
            if not isinstance(
                loop,
                (ast.For, ast.AsyncFor, ast.While),
            ):
                continue

            for node in ast.walk(loop):
                if not isinstance(node, ast.Compare):
                    continue

                if not any(
                    isinstance(op, (ast.In, ast.NotIn))
                    for op in node.ops
                ):
                    continue

                for comparator in node.comparators:
                    if not isinstance(
                        comparator,
                        (ast.List, ast.ListComp),
                    ):
                        continue

                    findings.append(
                        _finding(
                            context,
                            self.metadata.rule_id,
                            "Linear membership check inside loop",
                            (
                                "Membership against a list or list "
                                "comprehension may require linear "
                                "search on every iteration."
                            ),
                            node,
                            Severity.MEDIUM,
                            0.86,
                            (
                                "If membership is repeated and ordering "
                                "is not required, consider a set or "
                                "dictionary for average O(1) lookup."
                            ),
                        )
                    )

                    break

        return findings


class StringConcatenationRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PERF-PY-003",
        name="String Concatenation In Loop",
        description=(
            "Detects repeated string concatenation inside loops."
        ),
        category="performance",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings: list[Finding] = []

        for loop in ast.walk(tree):
            if not isinstance(
                loop,
                (ast.For, ast.AsyncFor, ast.While),
            ):
                continue

            for node in ast.walk(loop):
                if not isinstance(node, ast.AugAssign):
                    continue

                if not isinstance(node.op, ast.Add):
                    continue

                if not isinstance(node.target, ast.Name):
                    continue

                if not isinstance(
                    node.value,
                    (
                        ast.Str,
                        ast.JoinedStr,
                        ast.FormattedValue,
                    ),
                ):
                    continue

                findings.append(
                    _finding(
                        context,
                        self.metadata.rule_id,
                        "Repeated string concatenation",
                        (
                            "String concatenation is performed "
                            "inside a loop and may repeatedly "
                            "allocate strings."
                        ),
                        node,
                        Severity.LOW,
                        0.82,
                        (
                            "Consider collecting string fragments "
                            "and joining them once with ''.join(...)."
                        ),
                    )
                )

        return findings


class RepeatedExpensiveCallRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PERF-PY-004",
        name="Repeated Expensive Call",
        description=(
            "Detects selected potentially expensive operations "
            "performed repeatedly inside loops."
        ),
        category="performance",
    )

    EXPENSIVE_CALLS = {
        "sorted",
        "reversed",
    }

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings: list[Finding] = []

        for loop in ast.walk(tree):
            if not isinstance(
                loop,
                (ast.For, ast.AsyncFor, ast.While),
            ):
                continue

            for node in ast.walk(loop):
                if not isinstance(node, ast.Call):
                    continue

                if not isinstance(node.func, ast.Name):
                    continue

                if node.func.id not in self.EXPENSIVE_CALLS:
                    continue

                findings.append(
                    _finding(
                        context,
                        self.metadata.rule_id,
                        "Potentially expensive operation inside loop",
                        (
                            f"'{node.func.id}()' is executed inside "
                            "a loop and may repeat unnecessary work."
                        ),
                        node,
                        Severity.LOW,
                        0.78,
                        (
                            "Check whether the result can be computed "
                            "once outside the loop or cached."
                        ),
                    )
                )

        return findings


DEFAULT_PERFORMANCE_RULES = (
    NestedLoopRule,
    RepeatedMembershipRule,
    StringConcatenationRule,
    RepeatedExpensiveCallRule,
)
