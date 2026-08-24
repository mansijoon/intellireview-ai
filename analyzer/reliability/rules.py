from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext


class ReliabilityRule:
    """Base class for deterministic reliability rules."""

    rule_id: str = ""
    title: str = ""
    severity: str = "medium"
    confidence: float = 1.0
    remediation: str = ""

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[dict]:
        raise NotImplementedError


class BareExceptRule(ReliabilityRule):
    rule_id = "PY-REL-001"
    title = "Bare Except"
    severity = "high"
    remediation = (
        "Catch a specific exception type instead of using "
        "a bare except handler."
    )

    def analyze(self, context):
        findings = []

        if context.language.lower() != "python":
            return findings

        try:
            tree = ast.parse(context.source)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            if node.type is None:
                findings.append(
                    {
                        "rule_id": self.rule_id,
                        "title": self.title,
                        "description": (
                            "A bare except handler catches every "
                            "exception, including system-exiting "
                            "exceptions."
                        ),
                        "line_start": node.lineno,
                        "line_end": getattr(
                            node,
                            "end_lineno",
                            node.lineno,
                        ),
                        "severity": self.severity,
                        "confidence": self.confidence,
                        "remediation": self.remediation,
                    }
                )

        return findings


class BroadExceptionRule(ReliabilityRule):
    rule_id = "PY-REL-002"
    title = "Broad Exception Handler"
    severity = "medium"
    remediation = (
        "Catch the narrowest exception type that the operation "
        "can actually raise."
    )

    def analyze(self, context):
        findings = []

        if context.language.lower() != "python":
            return findings

        try:
            tree = ast.parse(context.source)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            if isinstance(node.type, ast.Name):
                is_broad = node.type.id in {
                    "Exception",
                    "BaseException",
                }
            elif isinstance(node.type, ast.Tuple):
                is_broad = any(
                    isinstance(item, ast.Name)
                    and item.id in {
                        "Exception",
                        "BaseException",
                    }
                    for item in node.type.elts
                )
            else:
                is_broad = False

            if not is_broad:
                continue

            exception_name = (
                "Exception"
                if isinstance(node.type, ast.Name)
                else "Exception/BaseException"
            )

            findings.append(
                {
                    "rule_id": self.rule_id,
                    "title": self.title,
                    "description": (
                        f"Handler catches broad {exception_name}, "
                        "which can hide unrelated failures."
                    ),
                    "line_start": node.lineno,
                    "line_end": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "remediation": self.remediation,
                }
            )

        return findings


class EmptyExceptionHandlerRule(ReliabilityRule):
    rule_id = "PY-REL-003"
    title = "Empty Exception Handler"
    severity = "high"
    remediation = (
        "Handle the exception explicitly or re-raise it after "
        "performing the required recovery action."
    )

    def analyze(self, context):
        findings = []

        if context.language.lower() != "python":
            return findings

        try:
            tree = ast.parse(context.source)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            statements = [
                statement
                for statement in node.body
                if not isinstance(
                    statement,
                    ast.Pass,
                )
            ]

            if statements:
                continue

            findings.append(
                {
                    "rule_id": self.rule_id,
                    "title": self.title,
                    "description": (
                        "The exception handler performs no "
                        "meaningful recovery or propagation."
                    ),
                    "line_start": node.lineno,
                    "line_end": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "remediation": self.remediation,
                }
            )

        return findings


class RaiseGenericExceptionRule(ReliabilityRule):
    rule_id = "PY-REL-004"
    title = "Generic Exception Raised"
    severity = "medium"
    remediation = (
        "Raise a specific exception type that communicates "
        "the actual failure condition."
    )

    def analyze(self, context):
        findings = []

        if context.language.lower() != "python":
            return findings

        try:
            tree = ast.parse(context.source)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise):
                continue

            if node.exc is None:
                continue

            exception_node = node.exc

            if isinstance(exception_node, ast.Call):
                exception_node = exception_node.func

            if not isinstance(exception_node, ast.Name):
                continue

            if exception_node.id not in {
                "Exception",
                "BaseException",
            }:
                continue

            findings.append(
                {
                    "rule_id": self.rule_id,
                    "title": self.title,
                    "description": (
                        f"Code raises generic "
                        f"{exception_node.id} instead of a "
                        "specific exception type."
                    ),
                    "line_start": node.lineno,
                    "line_end": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "remediation": self.remediation,
                }
            )

        return findings


DEFAULT_RELIABILITY_RULES = (
    BareExceptRule,
    BroadExceptionRule,
    EmptyExceptionHandlerRule,
    RaiseGenericExceptionRule,
)
