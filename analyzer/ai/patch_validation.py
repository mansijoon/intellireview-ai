from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PatchValidation:
    valid: bool
    syntax_valid: bool
    changed: bool
    reason: str


def validate_patch(
    original: str,
    patched: str,
) -> PatchValidation:

    if original == patched:
        return PatchValidation(
            valid=False,
            syntax_valid=False,
            changed=False,
            reason="Patch produced no source change.",
        )

    try:
        ast.parse(patched)
    except SyntaxError as exc:
        return PatchValidation(
            valid=False,
            syntax_valid=False,
            changed=True,
            reason=f"Patched source is invalid Python: {exc}",
        )

    return PatchValidation(
        valid=True,
        syntax_valid=True,
        changed=True,
        reason="Patch passed syntax validation.",
    )
