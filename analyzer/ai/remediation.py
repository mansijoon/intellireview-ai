from __future__ import annotations

from dataclasses import dataclass

from analyzer.ai.patch_generation import (
    GeneratedPatch,
    apply_patch,
    generate_patch,
)
from analyzer.ai.patch_validation import validate_patch
from analyzer.ai.regression import verify_regression


@dataclass(frozen=True, slots=True)
class RemediationResult:
    patch: GeneratedPatch
    patched_source: str
    valid: bool
    regression_free: bool
    reason: str


def remediate(
    *,
    file_path: str,
    source: str,
    original: str,
    replacement: str,
    reason: str,
) -> RemediationResult:
    patch = generate_patch(
        file_path=file_path,
        source=source,
        original=original,
        replacement=replacement,
        reason=reason,
    )

    patched_source = apply_patch(
        source,
        patch,
    )

    validation = validate_patch(
        source,
        patched_source,
    )

    if not validation.valid:
        return RemediationResult(
            patch=patch,
            patched_source=patched_source,
            valid=False,
            regression_free=False,
            reason=validation.reason,
        )

    regression = verify_regression(
        source,
        patched_source,
    )

    return RemediationResult(
        patch=patch,
        patched_source=patched_source,
        valid=validation.valid,
        regression_free=regression.passed,
        reason=regression.reason,
    )
