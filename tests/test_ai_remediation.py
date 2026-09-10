from analyzer.ai.remediation import generate_ai_remediation
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, text):
        self.text = text

    def generate_content(self, prompt):
        return FakeResponse(self.text)


def make_finding():
    return Finding(
        rule_id="PY-VAR-001",
        title="Unused variable",
        description="unused is assigned but never read.",
        severity=Severity.LOW,
        location=SourceLocation(
            file_path="review.py",
            line_start=2,
            line_end=2,
        ),
        analyzer="unused_variable_rule",
        confidence=0.97,
        remediation="Remove the unused variable.",
    )


def test_ai_remediation_generates_valid_patch():
    source = (
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    model = FakeModel(
        """{
            "original": "    unused = 10\\n",
            "replacement": "",
            "reason": "Remove the unused variable."
        }"""
    )

    result = generate_ai_remediation(
        model=model,
        source=source,
        finding=make_finding(),
    )

    assert result.valid is True
    assert result.regression_free is True
    assert result.patch is not None
    assert result.patched_source == (
        "def calculate():\n"
        "    return 42\n"
    )


def test_ai_remediation_rejects_wrong_location():
    source = (
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    model = FakeModel(
        """{
            "original": "    return 42\\n",
            "replacement": "    return 43\\n",
            "reason": "Change return value."
        }"""
    )

    result = generate_ai_remediation(
        model=model,
        source=source,
        finding=make_finding(),
    )

    assert result.valid is False
    assert result.regression_free is False
    assert result.patch is None
    assert "location" in result.reason


def test_ai_remediation_rejects_invalid_syntax():
    source = (
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    model = FakeModel(
        """{
            "original": "    unused = 10\\n",
            "replacement": "    unused = (\\n",
            "reason": "Test invalid patch."
        }"""
    )

    result = generate_ai_remediation(
        model=model,
        source=source,
        finding=make_finding(),
    )

    assert result.valid is False
    assert result.regression_free is False
    assert result.patch is not None
    assert "invalid Python" in result.reason


def test_ai_remediation_rejects_invalid_json():
    model = FakeModel("not json")

    result = generate_ai_remediation(
        model=model,
        source="x = 1\n",
        finding=make_finding(),
    )

    assert result.valid is False
    assert result.regression_free is False
    assert result.patch is None
