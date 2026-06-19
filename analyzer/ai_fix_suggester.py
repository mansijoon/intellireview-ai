from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()

USE_MOCK = False

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def generate_ai_fix_suggestions(
    code,
    findings
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
You are an expert software engineer performing a professional code review.

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

    response = model.generate_content(
        prompt
    )

    return response.text
