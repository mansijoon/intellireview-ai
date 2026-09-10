import analyzer.ai_fix_suggester as module


class FakeResponse:
    text = "AI fix suggestion"


class FakeModel:
    def generate_content(self, prompt):
        return FakeResponse()


def test_generate_ai_fix_suggestions_uses_model(monkeypatch):
    monkeypatch.setattr(module, "model", FakeModel())
    monkeypatch.setattr(module, "USE_MOCK", False)

    result = module.generate_ai_fix_suggestions(
        "password = 'admin123'",
        [
            {
                "type": "Hardcoded Password",
                "severity": "Critical",
            }
        ],
    )

    assert result == "AI fix suggestion"
