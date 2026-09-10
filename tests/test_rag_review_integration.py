from analyzer.core.models import SourceFile
from analyzer.knowledge.context import (
    RepositoryContextItem,
    RepositoryContextSelection,
)
import analyzer.review_engine as engine


class FakeReviewModel:
    def __init__(self):
        self.prompts = []

    def generate_content(self, prompt):
        self.prompts.append(prompt)

        class Response:
            text = """
{
  "findings": [],
  "readiness": {
    "production": "Good",
    "security": "Good",
    "maintainability": "Good",
    "scalability": "Good"
  },
  "quality_score": 90,
  "verdict": "No issues found."
}
"""

        return Response()


def test_repository_context_is_injected_into_ai_review(monkeypatch):
    fake_model = FakeReviewModel()

    monkeypatch.setattr(
        engine,
        "model",
        fake_model,
    )

    context = RepositoryContextSelection(
        query="security dependencies",
        items=(
            RepositoryContextItem(
                kind="file",
                identifier="file:auth.py",
                file_path="auth.py",
                name="auth.py",
                score=0.95,
                content=(
                    "def authenticate(user):\n"
                    "    return validate(user)\n"
                ),
            ),
        ),
    )

    monkeypatch.setattr(
        engine,
        "_build_repository_context",
        lambda repository_path, query: (
            "FILE: auth.py\n"
            "CODE:\n"
            "def authenticate(user):\n"
            "    return validate(user)\n"
        ),
    )

    # Ensure the test exercises the public review API.
    result = engine.review_code(
        "def review():\n    return True\n",
        repository_context=(
            "FILE: auth.py\n"
            "CODE:\n"
            "def authenticate(user):\n"
            "    return validate(user)\n"
        ),
    )

    assert result is not None
    assert len(fake_model.prompts) == 1
    assert "auth.py" in fake_model.prompts[0]
    assert "authenticate(user)" in fake_model.prompts[0]
    assert "validate(user)" in fake_model.prompts[0]
