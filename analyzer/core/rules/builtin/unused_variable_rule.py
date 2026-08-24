from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)
from analyzer.core.rules import AnalysisRule, RuleMetadata


class UnusedVariableRule(AnalysisRule):
    """Detect assigned names that are never read."""

    metadata = RuleMetadata(
        rule_id="PY-VAR-001",
        name="Unused Variable",
        description="Detects assigned names that are never read.",
        category="maintainability",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            exc = context.syntax_error

            if exc is None:
                return []

            line = max(1, exc.lineno or 1)

            return [
                Finding(
                    rule_id="PY-PARSE-001",
                    title="Python parse error",
                    description="Unable to parse the source file.",
                    severity=Severity.HIGH,
                    location=SourceLocation(
                        file_path=context.file_path,
                        line_start=line,
                        line_end=line,
                        column_start=(
                            exc.offset + 1
                            if exc.offset is not None
                            else None
                        ),
                    ),
                    analyzer="unused_variable_rule",
                    confidence=1.0,
                    remediation=(
                        "Fix the syntax error before analysis can continue."
                    ),
                )
            ]

        assigned: dict[str, ast.Name] = {}
        used: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    assigned[node.id] = node
                elif isinstance(node.ctx, ast.Load):
                    used.add(node.id)

        findings: list[Finding] = []

        for name, node in assigned.items():
            if name in used:
                continue

            line = max(1, getattr(node, "lineno", 1))
            end_line = max(
                line,
                getattr(node, "end_lineno", line),
            )

            column = getattr(node, "col_offset", None)

            findings.append(
                Finding(
                    rule_id=self.metadata.rule_id,
                    title="Unused variable",
                    description=(
                        f"{name} is assigned but never read."
                    ),
                    severity=Severity.LOW,
                    location=SourceLocation(
                        file_path=context.file_path,
                        line_start=line,
                        line_end=end_line,
                        column_start=(
                            column + 1
                            if column is not None
                            else None
                        ),
                    ),
                    analyzer="unused_variable_rule",
                    confidence=0.97,
                    remediation=(
                        f"Remove '{name}' if it is unnecessary, "
                        "or use it where appropriate."
                    ),
                )
            )

        return findings
