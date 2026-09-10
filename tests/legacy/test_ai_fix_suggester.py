from google.genai import errors

import analyzer.ai_fix_suggester as suggester


def test_mock_ai_fix_suggestions():
    suggester.USE_MOCK = True

    result = suggester.generate_ai_fix_suggestions("", [])

    assert "AI Fix Suggestions" in result


def test_gemini_quota_error_is_non_fatal(monkeypatch):
    suggester.USE_MOCK = False

    class FakeModel:
        def generate_content(self, prompt):
            raise errors.ClientError(
                429,
                {
                    "error": {
                        "code": 429,
                        "message": "quota exhausted",
                    }
                },
                None,
            )

    monkeypatch.setattr(suggester, "model", FakeModel())

    result = suggester.generate_ai_fix_suggestions(
        "print('test')",
        [],
    )

    assert "temporarily unavailable" in result
    assert "quota" in result
    assert "Deterministic IntelliReview analysis" in result
