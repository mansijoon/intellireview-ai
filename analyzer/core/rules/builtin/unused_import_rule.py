from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)
from analyzer.core.rules import AnalysisRule, RuleMetadata


class UnusedImportRule(AnalysisRule):
    """Detect imports that are not referenced by the source file."""

    metadata = RuleMetadata(
        rule_id="PY-IMPORT-001",
        name="Unused Import",
        description="Detects imported names that are never used.",
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
                    analyzer="unused_import_rule",
                    confidence=1.0,
                    remediation=(
                        "Fix the syntax error before analysis can continue."
                    ),
                )
            ]

        imported: dict[str, ast.alias] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = alias

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        continue

                    name = alias.asname or alias.name
                    imported[name] = alias

        used: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)

        findings: list[Finding] = []

        for name, alias in imported.items():
            if name in used:
                continue

            line = max(1, getattr(alias, "lineno", 1))
            end_line = max(
                line,
                getattr(alias, "end_lineno", line),
            )

            column = getattr(alias, "col_offset", None)

            findings.append(
                Finding(
                    rule_id=self.metadata.rule_id,
                    title="Unused import",
                    description=(
                        f"{name} is imported but never used."
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
                    analyzer="unused_import_rule",
                    confidence=0.99,
                    remediation=(
                        f"Remove the unused import '{name}' "
                        "unless it is intentionally imported for side effects."
                    ),
                )
            )

        return findings
