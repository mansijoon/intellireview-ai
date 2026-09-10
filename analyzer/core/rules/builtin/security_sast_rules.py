from __future__ import annotations

import ast

from analyzer.core.context import AnalysisContext
from analyzer.core.models import (
    Evidence,
    Finding,
)
from analyzer.core.rules import AnalysisRule, RuleMetadata


def _location(
    context: AnalysisContext,
    node: ast.AST,
):
    from analyzer.core.models import SourceLocation

    line_start = getattr(node, "lineno", 1)
    line_end = getattr(
        node,
        "end_lineno",
        line_start,
    )

    column_start = getattr(
        node,
        "col_offset",
        0,
    ) + 1

    column_end = getattr(
        node,
        "end_col_offset",
        None,
    )

    if column_end is not None:
        column_end += 1

    return SourceLocation(
        file_path=context.file_path,
        line_start=line_start,
        line_end=line_end,
        column_start=column_start,
        column_end=column_end,
    )


def _finding(
    context: AnalysisContext,
    node: ast.AST,
    *,
    rule_id: str,
    title: str,
    description: str,
    severity: str,
    confidence: float,
    remediation: str,
) -> Finding:
    source_segment = ast.get_source_segment(
        context.source,
        node,
    )

    evidence = ()

    if source_segment:
        evidence = (
            Evidence(
                message="Detected source expression.",
                location=_location(context, node),
                code_snippet=source_segment,
            ),
        )

    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=severity,
        confidence=confidence,
        location=_location(context, node),
        analyzer="security",
        remediation=remediation,
        evidence=evidence,
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


class DangerousEvalExecRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SAST-001",
        name="Dangerous eval/exec",
        description=(
            "Detects use of eval() or exec(), which execute "
            "dynamically supplied Python code."
        ),
        category="security",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _qualified_name(node.func)

            if name not in {"eval", "exec"}:
                continue

            findings.append(
                _finding(
                    context,
                    node,
                    rule_id=self.metadata.rule_id,
                    title="Dynamic code execution",
                    description=(
                        f"{name}() executes dynamically supplied "
                        "Python code and can create arbitrary "
                        "code-execution risk."
                    ),
                    severity="high",
                    confidence=0.98,
                    remediation=(
                        "Avoid dynamic code execution. Replace "
                        "eval/exec with explicit parsing or a "
                        "restricted data representation."
                    ),
                )
            )

        return findings


class ShellCommandExecutionRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SAST-002",
        name="Shell Command Execution",
        description=(
            "Detects direct use of os.system(), which executes "
            "commands through a system shell."
        ),
        category="security",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if _qualified_name(node.func) != "os.system":
                continue

            findings.append(
                _finding(
                    context,
                    node,
                    rule_id=self.metadata.rule_id,
                    title="Shell command execution",
                    description=(
                        "os.system() executes a command through "
                        "the operating-system shell."
                    ),
                    severity="high",
                    confidence=0.97,
                    remediation=(
                        "Prefer subprocess APIs with argument "
                        "lists and shell=False. Validate all "
                        "externally controlled arguments."
                    ),
                )
            )

        return findings


class UnsafeDeserializationRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SAST-003",
        name="Unsafe Deserialization",
        description=(
            "Detects pickle deserialization APIs that can execute "
            "attacker-controlled code."
        ),
        category="security",
    )

    UNSAFE_CALLS = {
        "pickle.load",
        "pickle.loads",
        "cPickle.load",
        "cPickle.loads",
    }

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _qualified_name(node.func)

            if name not in self.UNSAFE_CALLS:
                continue

            findings.append(
                _finding(
                    context,
                    node,
                    rule_id=self.metadata.rule_id,
                    title="Unsafe deserialization",
                    description=(
                        f"{name}() can deserialize attacker-"
                        "controlled data into executable Python "
                        "objects."
                    ),
                    severity="critical",
                    confidence=0.97,
                    remediation=(
                        "Do not deserialize untrusted data with "
                        "pickle. Use a safe data format such as "
                        "JSON with explicit validation."
                    ),
                )
            )

        return findings


class WeakCryptographyRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SAST-004",
        name="Weak Cryptography",
        description=(
            "Detects cryptographic algorithms that are generally "
            "considered unsuitable for security-sensitive use."
        ),
        category="security",
    )

    WEAK_CALLS = {
        "hashlib.md5",
        "hashlib.sha1",
    }

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _qualified_name(node.func)

            if name not in self.WEAK_CALLS:
                continue

            findings.append(
                _finding(
                    context,
                    node,
                    rule_id=self.metadata.rule_id,
                    title="Weak cryptographic algorithm",
                    description=(
                        f"{name} is not appropriate for "
                        "security-sensitive cryptographic use."
                    ),
                    severity="medium",
                    confidence=0.95,
                    remediation=(
                        "Use a modern cryptographic algorithm "
                        "appropriate for the security requirement, "
                        "such as SHA-256 for integrity hashing or "
                        "a dedicated password-hashing algorithm "
                        "for password storage."
                    ),
                )
            )

        return findings


class SubprocessShellTrueRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SAST-005",
        name="Subprocess shell=True",
        description=(
            "Detects subprocess calls explicitly configured to "
            "execute commands through a shell."
        ),
        category="security",
    )

    SUBPROCESS_CALLS = {
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
    }

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        tree = context.ast_tree

        if tree is None:
            return []

        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _qualified_name(node.func)

            if name not in self.SUBPROCESS_CALLS:
                continue

            shell_true = any(
                isinstance(keyword.value, ast.Constant)
                and keyword.arg == "shell"
                and keyword.value.value is True
                for keyword in node.keywords
            )

            if not shell_true:
                continue

            findings.append(
                _finding(
                    context,
                    node,
                    rule_id=self.metadata.rule_id,
                    title="Subprocess shell execution",
                    description=(
                        f"{name}(..., shell=True) executes the "
                        "command through a shell and can enable "
                        "command injection when arguments are "
                        "externally controlled."
                    ),
                    severity="high",
                    confidence=0.96,
                    remediation=(
                        "Avoid shell=True. Prefer an argument list "
                        "with shell=False and validate externally "
                        "controlled arguments."
                    ),
                )
            )

        return findings
