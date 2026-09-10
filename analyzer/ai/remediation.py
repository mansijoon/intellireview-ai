from __future__ import annotations

import json
from dataclasses import dataclass

from analyzer.ai.patch_generation import (
    GeneratedPatch,
    apply_patch,
    generate_patch,
)
from analyzer.ai.patch_validation import validate_patch
from analyzer.ai.regression import verify_regression
from analyzer.core.models import Finding


@dataclass(frozen=True, slots=True)
class RemediationResult:
    patch: GeneratedPatch | None
    patched_source: str
    valid: bool
    regression_free: bool
    reason: str


def _extract_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "AI remediation response does not contain JSON."
        )

    return text[start:end + 1]


def _build_prompt(
    *,
    source: str,
    finding: Finding,
) -> str:
    lines = source.splitlines()

    start = max(
        1,
        finding.location.line_start - 3,
    )

    end = min(
        len(lines),
        (finding.location.line_end or finding.location.line_start) + 3,
    )

    context = "\n".join(
        f"{number}: {lines[number - 1]}"
        for number in range(start, end + 1)
    )

    return f"""
Generate a minimal source-code fix for exactly this verified finding.

Finding:
{json.dumps({
    "rule_id": finding.rule_id,
    "title": finding.title,
    "description": finding.description,
    "severity": finding.severity.value,
    "file": finding.location.file_path,
    "line_start": finding.location.line_start,
    "line_end": finding.location.line_end,
    "remediation": finding.remediation,
}, indent=2)}

Relevant source:
{context}

Rules:
- Fix only the specified finding.
- Do not invent unrelated changes.
- Preserve existing behavior unless the finding requires behavior change.
- The original field must be an exact substring of the source.
- The replacement may be empty for deletion.
- Keep the patch minimal.
- Return ONLY JSON.

Schema:
{{
  "original": "exact source text to replace",
  "replacement": "replacement source text",
  "reason": "why this fixes the finding"
}}
""".strip()


def generate_ai_remediation(
    *,
    model,
    source: str,
    finding: Finding,
) -> RemediationResult:
    response = model.generate_content(
        _build_prompt(
            source=source,
            finding=finding,
        )
    )

    try:
        data = json.loads(
            _extract_json(response.text)
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return RemediationResult(
            patch=None,
            patched_source=source,
            valid=False,
            regression_free=False,
            reason=f"Invalid AI remediation response: {exc}",
        )

    original = data.get("original")
    replacement = data.get("replacement")
    reason = data.get("reason")

    if not isinstance(original, str):
        return RemediationResult(
            patch=None,
            patched_source=source,
            valid=False,
            regression_free=False,
            reason="AI remediation did not provide valid original code.",
        )

    if not isinstance(replacement, str):
        return RemediationResult(
            patch=None,
            patched_source=source,
            valid=False,
            regression_free=False,
            reason="AI remediation did not provide valid replacement code.",
        )

    if not isinstance(reason, str) or not reason.strip():
        return RemediationResult(
            patch=None,
            patched_source=source,
            valid=False,
            regression_free=False,
            reason="AI remediation did not provide a valid reason.",
        )

    try:
        patch = generate_patch(
            file_path=finding.location.file_path,
            source=source,
            original=original,
            replacement=replacement,
            reason=reason,
            line_start=finding.location.line_start,
            line_end=(
                finding.location.line_end
                or finding.location.line_start
            ),
        )

        patched_source = apply_patch(
            source,
            patch,
        )
    except ValueError as exc:
        return RemediationResult(
            patch=None,
            patched_source=source,
            valid=False,
            regression_free=False,
            reason=f"AI patch rejected: {exc}",
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
