from __future__ import annotations

from dataclasses import dataclass

from analyzer.ai.structured_output import StructuredFinding


@dataclass(frozen=True, slots=True)
class VerifiedFinding:
    finding: StructuredFinding
    verified: bool
    verification_score: float
    reason: str


def verify_finding(
    finding: StructuredFinding,
    static_findings: list,
) -> VerifiedFinding:
    if not static_findings:
        return VerifiedFinding(
            finding=finding,
            verified=False,
            verification_score=0.0,
            reason="No deterministic finding supports this AI finding.",
        )

    category = finding.category.lower()
    explanation = finding.explanation.lower()

    matches = 0

    for static_finding in static_findings:
        text = str(static_finding).lower()

        if category in text:
            matches += 1
            continue

        category_terms = category.split()

        if any(term in text for term in category_terms):
            matches += 1
            continue

        if any(
            term in explanation
            for term in (
                "security",
                "performance",
                "complexity",
                "unused",
                "duplicate",
                "secret",
            )
            if term in text
        ):
            matches += 1

    if matches == 0:
        return VerifiedFinding(
            finding=finding,
            verified=False,
            verification_score=0.0,
            reason="No matching deterministic evidence.",
        )

    score = min(
        1.0,
        0.5 + (0.1 * matches),
    )

    return VerifiedFinding(
        finding=finding,
        verified=True,
        verification_score=score,
        reason=(
            f"Matched {matches} deterministic "
            "finding(s)."
        ),
    )


def verify_findings(
    findings: tuple[StructuredFinding, ...],
    static_findings: list,
) -> tuple[VerifiedFinding, ...]:
    return tuple(
        verify_finding(
            finding,
            static_findings,
        )
        for finding in findings
    )
