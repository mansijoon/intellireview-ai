from __future__ import annotations

from dataclasses import dataclass

from analyzer.ai.structured_output import StructuredFinding
from analyzer.core.models import Finding


@dataclass(frozen=True, slots=True)
class VerifiedFinding:
    finding: StructuredFinding
    verified: bool
    verification_score: float
    reason: str
    supporting_findings: tuple[Finding, ...] = ()


def _normalize(value: str) -> str:
    return " ".join(
        value.lower().strip().split()
    )


def _finding_matches(
    ai_finding: StructuredFinding,
    canonical: Finding,
) -> tuple[int, list[str]]:
    score = 0
    matches: list[str] = []

    category = _normalize(ai_finding.category)
    explanation = _normalize(ai_finding.explanation)

    title = _normalize(canonical.title)
    description = _normalize(canonical.description)

    if category and (
        category in title
        or category in description
    ):
        score += 2
        matches.append("category")

    if title and (
        title in explanation
        or any(
            term in explanation
            for term in title.split()
            if len(term) >= 4
        )
    ):
        score += 2
        matches.append("title")

    if description:
        description_terms = [
            term
            for term in description.split()
            if len(term) >= 5
        ]

        matching_terms = sum(
            term in explanation
            for term in description_terms
        )

        if matching_terms >= 2:
            score += 2
            matches.append("description")

    if (
        _normalize(ai_finding.severity)
        == _normalize(canonical.severity.value)
    ):
        score += 1
        matches.append("severity")

    return score, matches


def verify_finding(
    finding: StructuredFinding,
    canonical_findings: tuple[Finding, ...],
) -> VerifiedFinding:
    if not canonical_findings:
        return VerifiedFinding(
            finding=finding,
            verified=False,
            verification_score=0.0,
            reason=(
                "No canonical deterministic finding "
                "supports this AI finding."
            ),
        )

    candidates: list[
        tuple[int, Finding, list[str]]
    ] = []

    for canonical in canonical_findings:
        score, matches = _finding_matches(
            finding,
            canonical,
        )

        if score > 0:
            candidates.append(
                (score, canonical, matches)
            )

    if not candidates:
        return VerifiedFinding(
            finding=finding,
            verified=False,
            verification_score=0.0,
            reason=(
                "No matching canonical deterministic "
                "evidence."
            ),
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1].location.file_path,
            item[1].location.line_start,
            item[1].rule_id,
        )
    )

    best_score, best_finding, matches = candidates[0]

    verification_score = min(
        1.0,
        best_score / 7.0,
    )

    strong_match = (
        "category" in matches and "title" in matches
    ) or (
        "category" in matches and "description" in matches
    ) or (
        "title" in matches and "description" in matches
    )

    if not strong_match:
        return VerifiedFinding(
            finding=finding,
            verified=False,
            verification_score=verification_score,
            reason=(
                "Canonical evidence was found, but the "
                "match lacks sufficient independent evidence."
            ),
            supporting_findings=(best_finding,),
        )

    return VerifiedFinding(
        finding=finding,
        verified=True,
        verification_score=verification_score,
        reason=(
            "Matched canonical finding "
            f"{best_finding.rule_id} at "
            f"{best_finding.location.file_path}:"
            f"{best_finding.location.line_start} "
            f"using {', '.join(matches)}."
        ),
        supporting_findings=(best_finding,),
    )


def verify_findings(
    findings: tuple[StructuredFinding, ...],
    canonical_findings: tuple[Finding, ...],
) -> tuple[VerifiedFinding, ...]:
    return tuple(
        verify_finding(
            finding,
            canonical_findings,
        )
        for finding in findings
    )
