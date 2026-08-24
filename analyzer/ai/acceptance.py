from __future__ import annotations

from dataclasses import dataclass

from analyzer.ai.verification import VerifiedFinding


@dataclass(frozen=True, slots=True)
class AcceptedFinding:
    finding: VerifiedFinding
    accepted: bool
    reason: str


MIN_CONFIDENCE = 0.70
MIN_VERIFICATION_SCORE = 0.50


def accept_finding(
    finding: VerifiedFinding,
) -> AcceptedFinding:

    if not finding.verified:
        return AcceptedFinding(
            finding=finding,
            accepted=False,
            reason="Finding failed deterministic verification.",
        )

    if finding.finding.confidence < MIN_CONFIDENCE:
        return AcceptedFinding(
            finding=finding,
            accepted=False,
            reason=(
                "Finding confidence is below "
                f"{MIN_CONFIDENCE:.2f}."
            ),
        )

    if finding.verification_score < MIN_VERIFICATION_SCORE:
        return AcceptedFinding(
            finding=finding,
            accepted=False,
            reason=(
                "Verification score is below "
                f"{MIN_VERIFICATION_SCORE:.2f}."
            ),
        )

    return AcceptedFinding(
        finding=finding,
        accepted=True,
        reason="Finding passed confidence and verification thresholds.",
    )


def accept_findings(
    findings: tuple[VerifiedFinding, ...],
) -> tuple[AcceptedFinding, ...]:
    return tuple(
        accept_finding(finding)
        for finding in findings
    )
