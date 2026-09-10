import analyzer.review_engine as engine


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeReviewModel:
    def generate_content(self, prompt):
        if "Generate a minimal source-code fix" in prompt:
            return FakeResponse(
                """{
                    "original": "    unused = 10\\n",
                    "replacement": "",
                    "reason": "Remove the unused variable."
                }"""
            )

        return FakeResponse(
            """{
                "findings": [
                    {
                        "category": "Unused Variable",
                        "severity": "Low",
                        "explanation": "unused is assigned but never read.",
                        "recommendation": "Remove the unused variable.",
                        "confidence": 0.95
                    }
                ],
                "readiness": {
                    "production": "Good",
                    "security": "Good",
                    "maintainability": "Good",
                    "scalability": "Good"
                },
                "quality_score": 90,
                "verdict": "Minor maintainability issue."
            }"""
        )


def test_review_code_does_not_generate_remediation_by_default():
    engine.model = FakeReviewModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    assert result["findings"]
    assert result["remediations"] == ()


def test_review_code_generates_remediation_only_for_accepted_findings():
    engine.model = FakeReviewModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n",
        generate_remediations=True,
    )

    assert len(result["findings"]) == 1
    assert len(result["remediations"]) == 1

    remediation = result["remediations"][0]

    assert remediation.valid is True
    assert remediation.regression_free is True
    assert remediation.patch is not None

    assert remediation.patched_source == (
        "def calculate():\n"
        "    return 42\n"
    )


class FakeUnrelatedModel:
    def generate_content(self, prompt):
        return FakeResponse(
            """{
                "findings": [
                    {
                        "category": "SQL Injection",
                        "severity": "High",
                        "explanation": "User input can reach a database query.",
                        "recommendation": "Use parameterized queries.",
                        "confidence": 0.95
                    }
                ],
                "readiness": {
                    "production": "Good",
                    "security": "Good",
                    "maintainability": "Good",
                    "scalability": "Good"
                },
                "quality_score": 90,
                "verdict": "Security review."
            }"""
        )


def test_rejected_ai_finding_cannot_trigger_remediation():
    engine.model = FakeUnrelatedModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n",
        generate_remediations=True,
    )

    assert result["findings"] == ()
    assert result["remediations"] == ()


def test_validated_remediation_is_attached_to_canonical_finding():
    engine.model = FakeReviewModel()

    result = engine.review_code(
        """
def calculate():
    unused = 10
    return 42
""",
        generate_remediations=True,
    )

    assert len(result["findings"]) == 1

    finding = result["findings"][0]

    assert finding.rule_id == "PY-VAR-001"
    assert finding.suggested_patch == ""


def test_review_code_generates_tests_only_when_enabled():
    engine.model = FakeReviewModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n",
        generate_tests=True,
    )

    assert len(result["findings"]) == 1
    assert len(result["generated_tests"]) == 1

    generated = result["generated_tests"][0]

    assert generated.file_path == "review.py"
    assert generated.target == "calculate"
    assert "test_calculate_generated" in generated.test_code


def test_review_code_does_not_generate_tests_by_default():
    engine.model = FakeReviewModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n",
    )

    assert result["generated_tests"] == ()


def test_rejected_ai_finding_cannot_trigger_test_generation():
    engine.model = FakeUnrelatedModel()

    result = engine.review_code(
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n",
        generate_tests=True,
    )

    assert result["findings"] == ()
    assert result["generated_tests"] == ()
