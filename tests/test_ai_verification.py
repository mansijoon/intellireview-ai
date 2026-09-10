from analyzer.ai.structured_output import StructuredFinding
from analyzer.ai.verification import verify_finding
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)


def canonical_finding():
    return Finding(
        rule_id="PY-VAR-001",
        title="Unused variable",
        description="unused is assigned but never read.",
        severity=Severity.LOW,
        location=SourceLocation(
            file_path="review.py",
            line_start=3,
        ),
        analyzer="unused_variable_rule",
        confidence=0.97,
    )


def test_strong_ai_finding_is_verified():
    finding = StructuredFinding(
        category="Unused Variable",
        severity="Low",
        explanation=(
            "The unused variable is assigned "
            "but never read."
        ),
        recommendation="Remove the unused variable.",
        confidence=0.95,
    )

    result = verify_finding(
        finding,
        (canonical_finding(),),
    )

    assert result.verified is True
    assert result.supporting_findings == (
        canonical_finding(),
    )


def test_unrelated_ai_finding_is_rejected():
    finding = StructuredFinding(
        category="SQL Injection",
        severity="High",
        explanation=(
            "User input can reach a database query."
        ),
        recommendation="Use parameterized queries.",
        confidence=0.95,
    )

    result = verify_finding(
        finding,
        (canonical_finding(),),
    )

    assert result.verified is False
    assert result.supporting_findings == ()


def test_category_only_match_is_rejected():
    finding = StructuredFinding(
        category="Unused Variable",
        severity="Low",
        explanation="This is an issue.",
        recommendation="Fix it.",
        confidence=0.95,
    )

    result = verify_finding(
        finding,
        (canonical_finding(),),
    )

    assert result.verified is False
    assert result.supporting_findings == (
        canonical_finding(),
    )


def test_no_canonical_findings_rejects_ai_finding():
    finding = StructuredFinding(
        category="Unused Variable",
        severity="Low",
        explanation=(
            "The unused variable is never read."
        ),
        recommendation="Remove it.",
        confidence=0.95,
    )

    result = verify_finding(
        finding,
        (),
    )

    assert result.verified is False
    assert result.verification_score == 0.0
    assert result.supporting_findings == ()
