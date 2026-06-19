from dotenv import load_dotenv
import google.generativeai as genai
import os

from analyzer.prompts import REVIEW_PROMPT

from analyzer.static_analysis import (
    run_static_analysis
)

from analyzer.static_formatter import (
    format_static_findings
)

load_dotenv()

USE_MOCK = False

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def review_code(code: str):

    if USE_MOCK:

        print("MOCK MODE ENABLED")

        with open(
            "mock_review.txt",
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

    static_findings = run_static_analysis(
        code
    )

    static_report = format_static_findings(
        static_findings
    )

    prompt = REVIEW_PROMPT.format(
        code=code
    )

    prompt += f"""

    Detected Static Analysis Findings:

    {static_report}

    Explain:

    1. Why these findings matter
    2. Security implications
    3. Performance implications
    4. Maintainability implications
    5. Recommended fixes
    """
    
    
    response = model.generate_content(
        prompt
    )

    return response.text
