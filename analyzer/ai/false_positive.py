from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from analyzer.ai.acceptance import AcceptedFinding


class FindingDisposition(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class FindingDecision:
    finding: AcceptedFinding
    disposition: FindingDisposition
    reason: str


REVIEW_CONFIDENCE_THRESHOLD = 0.50


def classify_finding(
    finding: AcceptedFinding,
) -> FindingDecision:

    if finding.accepted:
        return FindingDecision(
            finding=finding,
            disposition=FindingDisposition.ACCEPT,
            reason="Finding passed verification and confidence checks.",
        )

    confidence = finding.finding.finding.confidence

    if confidence >= REVIEW_CONFIDENCE_THRESHOLD:
        return FindingDecision(
            finding=finding,
            disposition=FindingDisposition.REVIEW,
            reason=(
                "Finding was not automatically accepted; "
                "manual review is recommended."
            ),
        )

    return FindingDecision(
        finding=finding,
        disposition=FindingDisposition.REJECT,
        reason="Finding confidence is too low to retain.",
    )


def classify_findings(
    findings: tuple[AcceptedFinding, ...],
) -> tuple[FindingDecision, ...]:
    return tuple(
        classify_finding(finding)
        for finding in findings
    )
