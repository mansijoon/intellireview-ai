from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors


load_dotenv()

USE_MOCK = False

class _GeminiModel:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is required for AI fix suggestions"
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def generate_content(self, prompt):
        return self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )


model = _GeminiModel()


def generate_ai_fix_suggestions(
    code,
    findings,
):
    if USE_MOCK:
        return """
## AI Fix Suggestions

### Hardcoded Password

Current:

password = "admin123"

Suggested:

import os

password = os.getenv(
    "PASSWORD"
)

Reason:

Credentials should not be stored in source code.
"""

    prompt = f"""
You are a Senior Google Software Engineer.

Source Code:

{code}

Detected Issues:

{findings}

Provide:

1. Specific fixes
2. Improved code examples
3. Security improvements
4. Performance improvements
5. Refactoring suggestions

Format the response in Markdown.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except errors.ClientError as exc:
        if getattr(exc, "code", None) == 429:
            return (
                "## AI Fix Suggestions\n\n"
                "AI fix suggestions are temporarily unavailable because "
                "the Gemini API quota has been exhausted.\n\n"
                "Deterministic IntelliReview analysis is still available."
            )
        raise
