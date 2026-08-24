from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegressionVerification:
    passed: bool
    syntax_valid: bool
    original_syntax_valid: bool
    reason: str


def verify_regression(
    original: str,
    patched: str,
) -> RegressionVerification:

    try:
        ast.parse(original)
        original_valid = True
    except SyntaxError:
        original_valid = False

    if not original_valid:
        return RegressionVerification(
            passed=False,
            syntax_valid=False,
            original_syntax_valid=False,
            reason="Original source is already syntactically invalid.",
        )

    try:
        ast.parse(patched)
        patched_valid = True
    except SyntaxError:
        patched_valid = False

    if not patched_valid:
        return RegressionVerification(
            passed=False,
            syntax_valid=False,
            original_syntax_valid=True,
            reason="Patch introduced a syntax regression.",
        )

    return RegressionVerification(
        passed=True,
        syntax_valid=True,
        original_syntax_valid=True,
        reason="Patched source passed regression syntax verification.",
    )
