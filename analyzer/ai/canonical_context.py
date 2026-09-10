from __future__ import annotations

from analyzer.core.models import Finding


def serialize_finding(
    finding: Finding,
) -> dict:
    return {
        "rule_id": finding.rule_id,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity.value,
        "file": finding.location.file_path,
        "line_start": finding.location.line_start,
        "line_end": finding.location.line_end,
        "column_start": finding.location.column_start,
        "column_end": finding.location.column_end,
        "confidence": finding.confidence,
        "analyzer": finding.analyzer,
        "remediation": finding.remediation,
        "evidence": [
            {
                "message": evidence.message,
                "file": (
                    evidence.location.file_path
                    if evidence.location
                    else None
                ),
                "line_start": (
                    evidence.location.line_start
                    if evidence.location
                    else None
                ),
                "line_end": (
                    evidence.location.line_end
                    if evidence.location
                    else None
                ),
                "code_snippet": evidence.code_snippet,
            }
            for evidence in finding.evidence
        ],
    }


def build_canonical_context(
    findings: tuple[Finding, ...],
) -> list[dict]:
    return [
        serialize_finding(finding)
        for finding in findings
    ]
