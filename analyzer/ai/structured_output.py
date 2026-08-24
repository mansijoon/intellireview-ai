from __future__ import annotations

import json
from dataclasses import dataclass


_ALLOWED_SEVERITIES = frozenset(
    {"Critical", "High", "Medium", "Low"}
)


@dataclass(frozen=True, slots=True)
class StructuredFinding:
    category: str
    severity: str
    explanation: str
    recommendation: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("category must not be empty")

        if self.severity not in _ALLOWED_SEVERITIES:
            raise ValueError(
                f"invalid severity: {self.severity}"
            )

        if not self.explanation.strip():
            raise ValueError(
                "explanation must not be empty"
            )

        if not self.recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )


@dataclass(frozen=True, slots=True)
class StructuredReview:
    findings: tuple[StructuredFinding, ...]
    production_readiness: str
    security_readiness: str
    maintainability: str
    scalability: str
    quality_score: float
    verdict: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality_score <= 100.0:
            raise ValueError(
                "quality_score must be between 0 and 100"
            )

        if not self.verdict.strip():
            raise ValueError(
                "verdict must not be empty"
            )


def parse_structured_review(
    response_text: str,
) -> StructuredReview:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM response is not valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "LLM response must be a JSON object"
        )

    findings_payload = payload.get(
        "findings",
        [],
    )

    if not isinstance(findings_payload, list):
        raise ValueError(
            "findings must be a list"
        )

    readiness = payload.get("readiness")

    if not isinstance(readiness, dict):
        raise ValueError(
            "readiness must be an object"
        )

    findings = tuple(
        StructuredFinding(
            category=str(item["category"]),
            severity=str(item["severity"]),
            explanation=str(item["explanation"]),
            recommendation=str(item["recommendation"]),
            confidence=float(item["confidence"]),
        )
        for item in findings_payload
    )

    return StructuredReview(
        findings=findings,
        production_readiness=str(
            readiness["production"]
        ),
        security_readiness=str(
            readiness["security"]
        ),
        maintainability=str(
            readiness["maintainability"]
        ),
        scalability=str(
            readiness["scalability"]
        ),
        quality_score=float(
            payload["quality_score"]
        ),
        verdict=str(payload["verdict"]),
    )
