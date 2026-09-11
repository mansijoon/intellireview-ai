from __future__ import annotations

import json
import os
from dataclasses import replace

from dotenv import load_dotenv
from google import genai

from analyzer.ai.acceptance import accept_findings
from analyzer.ai.canonical_context import build_canonical_context
from analyzer.ai.remediation import generate_ai_remediation
from analyzer.ai.test_generation import generate_test_for_finding
from analyzer.ai.false_positive import classify_findings
from analyzer.ai.structured_output import parse_structured_review
from analyzer.ai.verification import verify_findings
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext
from analyzer.static.repository_analyzer import StaticRepositoryAnalyzer
from analyzer.prompts import REVIEW_PROMPT


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
                    "GEMINI_API_KEY is required for AI review"
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def generate_content(self, prompt):
        return self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )


model = _GeminiModel()


def _build_repository_context(
    repository_path: str,
    query: str,
) -> str:
    return ""


def _build_code_repository(
    code: str,
) -> RepositoryContext:
    import hashlib

    source_file = SourceFile(
        path="review.py",
        content_hash=hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest(),
        language="python",
        size_bytes=len(code.encode("utf-8")),
        line_count=len(code.splitlines()),
    )

    return RepositoryContext(
        repository_id="ai-review",
        revision="working-tree",
        root_path=".",
        files=(source_file,),
        source_contents={
            "review.py": code,
        },
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
    *,
    generate_remediations: bool = False,
    generate_tests: bool = False,
    repository_context: str = "",
):
    if USE_MOCK:
        print("MOCK MODE ENABLED")

        with open(
            "mock_review.txt",
            "r",
            encoding="utf-8",
        ) as f:
            return f.read()

    repository = _build_code_repository(code)

    static_result = StaticRepositoryAnalyzer().analyze(
        repository
    )

    if static_result.status.value != "success":
        raise RuntimeError(
            "Canonical deterministic analysis failed."
        )

    canonical_findings = tuple(
        static_result.artifacts.get(
            "findings",
            (),
        )
    )


    prompt = REVIEW_PROMPT.format(
        code=code
    )

    prompt += f"""

Repository-Aware Context:

{repository_context}

Canonical Deterministic Findings:

{json.dumps(
    build_canonical_context(canonical_findings),
    indent=2,
)}

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
- Do not invent findings unsupported by the source code or canonical deterministic analysis.
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
        canonical_findings,
    )

    accepted = accept_findings(
        verified
    )

    decisions = classify_findings(
        accepted
    )

    accepted_canonical_findings = tuple(
        decision.finding.finding.supporting_findings[0]
        for decision in decisions
        if (
            decision.disposition.value == "accept"
            and decision.finding.finding.supporting_findings
        )
    )

    accepted_findings = accepted_canonical_findings

    remediation_results = ()
    generated_tests = ()

    if generate_remediations:

        generated_remediations = tuple(
            generate_ai_remediation(
                model=model,
                source=code,
                finding=finding,
            )
            for finding in accepted_canonical_findings
        )

        remediation_results = generated_remediations

        remediation_by_rule_id = {}

        for finding, remediation in zip(
            accepted_canonical_findings,
            generated_remediations,
        ):
            if (
                remediation.valid
                and remediation.regression_free
                and remediation.patch is not None
            ):
                remediation_by_rule_id[
                    finding.rule_id
                ] = remediation

        canonical_findings = tuple(
            replace(
                finding,
                suggested_patch=(
                    remediation_by_rule_id[
                        finding.rule_id
                    ].patch.replacement
                )
                if finding.rule_id in remediation_by_rule_id
                else finding.suggested_patch,
            )
            for finding in canonical_findings
        )

        accepted_findings = tuple(
            replace(
                finding,
                suggested_patch=(
                    remediation_by_rule_id[
                        finding.rule_id
                    ].patch.replacement
                )
                if finding.rule_id in remediation_by_rule_id
                else finding.suggested_patch,
            )
            for finding in accepted_canonical_findings
        )

        accepted_canonical_findings = accepted_findings

    if generate_tests:
        generated_test_results = []

        for finding in accepted_findings:
            try:
                generated_test = generate_test_for_finding(
                    source=code,
                    file_path=finding.location.file_path,
                    line_start=finding.location.line_start,
                )
            except (SyntaxError, ValueError):
                continue

            generated_test_results.append(
                generated_test
            )

        generated_tests = tuple(
            generated_test_results
        )

    return {
        "review": structured,
        "findings": accepted_findings,
        "finding_decisions": decisions,
        "static_findings": canonical_findings,
        "repository_context": repository_context,
        "remediations": remediation_results,
        "generated_tests": generated_tests,
    }
