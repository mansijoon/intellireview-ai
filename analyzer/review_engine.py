from __future__ import annotations

import json
import os

from dotenv import load_dotenv
import google.generativeai as genai

from analyzer.ai.acceptance import accept_findings
from analyzer.ai.false_positive import classify_findings
from analyzer.ai.structured_output import parse_structured_review
from analyzer.ai.verification import verify_findings
from analyzer.core import RepositoryLoader
from analyzer.knowledge import (
    KnowledgeRepositoryAnalyzer,
    format_repository_context,
    select_repository_context,
)
from analyzer.prompts import REVIEW_PROMPT
from analyzer.static_analysis import run_static_analysis
from analyzer.static_formatter import format_static_findings


load_dotenv()

USE_MOCK = False

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def _build_repository_context(
    repository_path: str,
    query: str,
) -> str:
    repository = RepositoryLoader().load(
        repository_path,
        repository_id="ai-review",
        revision="working-tree",
    )

    result = KnowledgeRepositoryAnalyzer().analyze(
        repository
    )

    if result.status.value != "success":
        return ""

    knowledge = result.artifacts["knowledge_model"]

    selection = select_repository_context(
        knowledge,
        query,
        limit=8,
    )

    return format_repository_context(
        selection,
        max_total_chars=30000,
    )


def _extract_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "LLM response does not contain a JSON object"
        )

    return text[start:end + 1]


def review_code(
    code: str,
    repository_path: str = ".",
):
    if USE_MOCK:
        print("MOCK MODE ENABLED")

        with open(
            "mock_review.txt",
            "r",
            encoding="utf-8",
        ) as f:
            return f.read()

    static_findings = run_static_analysis(code)

    static_report = format_static_findings(
        static_findings
    )

    repository_context = _build_repository_context(
        repository_path,
        "code review analyze security performance architecture",
    )

    prompt = REVIEW_PROMPT.format(
        code=code
    )

    prompt += f"""

Repository-Aware Context:

{repository_context}

Detected Static Analysis Findings:

{static_report}

Return ONLY valid JSON.

Required schema:

{{
  "findings": [
    {{
      "category": "Security",
      "severity": "High",
      "explanation": "Specific explanation.",
      "recommendation": "Specific recommendation.",
      "confidence": 0.95
    }}
  ],
  "readiness": {{
    "production": "Good",
    "security": "Good",
    "maintainability": "Good",
    "scalability": "Good"
  }},
  "quality_score": 85,
  "verdict": "Final assessment."
}}

Rules:
- Do not invent findings unsupported by the source code or deterministic analysis.
- Use repository context only when relevant.
- Confidence must be between 0 and 1.
- Severity must be Critical, High, Medium, or Low.
- Do not duplicate deterministic findings.
"""

    response = model.generate_content(prompt)

    structured = parse_structured_review(
        _extract_json(response.text)
    )

    verified = verify_findings(
        structured.findings,
        static_findings,
    )

    accepted = accept_findings(verified)

    decisions = classify_findings(accepted)

    accepted_findings = tuple(
        decision.finding.finding.finding
        for decision in decisions
        if decision.disposition.value == "accept"
    )

    return {
        "review": structured,
        "findings": accepted_findings,
        "finding_decisions": decisions,
        "static_findings": static_findings,
        "repository_context": repository_context,
    }
