from __future__ import annotations

import hashlib

from analyzer.core.context import AnalysisContext
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext
from analyzer.static.repository_analyzer import StaticRepositoryAnalyzer
from analyzer.core.rules.defaults import create_default_registry


def _build_code_repository(
    code: str,
    *,
    file_path: str = "review.py",
) -> RepositoryContext:
    content_hash = hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()

    source_file = SourceFile(
        path=file_path,
        content_hash=content_hash,
        size_bytes=len(code.encode("utf-8")),
        line_count=len(code.splitlines()),
        language="python",
    )

    return RepositoryContext(
        repository_id="pr-review",
        revision="working-tree",
        root_path=".",
        files=(source_file,),
        source_contents={
            file_path: code,
        },
    )


def _finding_to_dict(
    finding,
) -> dict:
    title = finding.title

    compatibility_titles = {
        "Unused import": "Unused Import",
        "Unused variable": "Unused Variable",
    }

    title = compatibility_titles.get(
        title,
        title,
    )

    return {
        "type": title,
        "severity": finding.severity.value,
        "message": finding.description,
        "line": finding.location.line_start,
    }


def _review_code_findings(
    code: str,
    *,
    file_path: str = "review.py",
) -> list[dict]:
    repository = _build_code_repository(
        code,
        file_path=file_path,
    )

    registry = create_default_registry()

    rules = list(
        registry.create_rules()
    )

    findings = []

    for context in repository.iter_contexts():
        for rule in rules:
            findings.extend(
                rule.analyze(context)
            )

    return [
        _finding_to_dict(finding)
        for finding in findings
    ]

    if result.status.value != "success":
        raise RuntimeError(
            "Canonical deterministic PR analysis failed."
        )

    findings = result.artifacts.get(
        "findings",
        (),
    )

    return [
        _finding_to_dict(finding)
        for finding in findings
    ]


def review_code(
    code: str,
) -> list[dict]:
    """
    Run the canonical deterministic review engine.

    The returned dictionary format is preserved for compatibility
    with existing CLI and GitHub PR workflows.
    """

    return _review_code_findings(code)


def _extract_added_code(
    diff_text: str,
) -> str:
    added_lines: list[str] = []

    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    return "\n".join(added_lines)


def review_pull_request(
    diff_text: str,
) -> list[dict]:
    """
    Review added code in a unified PR diff.
    """

    return review_code(
        _extract_added_code(diff_text)
    )


def review_pull_request_files(
    files: list[dict],
) -> list[dict]:
    """
    Review each changed PR file independently using the
    canonical deterministic engine.
    """

    findings: list[dict] = []

    for file in files:
        path = file.get("filename", "")
        patch = file.get("patch")

        if not path or not patch:
            continue

        added_code = _extract_added_code(patch)

        if not added_code.strip():
            continue

        file_findings = _review_code_findings(
            added_code,
            file_path=path,
        )

        for finding in file_findings:
            finding["file_path"] = path
            findings.append(finding)

    return findings
