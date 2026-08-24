from __future__ import annotations

from typing import Any

from analyzer.core.context import AnalysisContext
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)


_SEVERITY_MAP = {
    "info": Severity.INFO,
    "low": Severity.LOW,
    "medium": Severity.MEDIUM,
    "high": Severity.HIGH,
    "critical": Severity.CRITICAL,
}


def convert_legacy_finding(
    finding: Any,
    context: AnalysisContext,
    *,
    rule_id: str,
    analyzer: str,
    index: int,
    default_title: str = "Static analysis finding",
) -> Finding:
    if isinstance(finding, dict):
        message = (
            finding.get("message")
            or finding.get("description")
            or finding.get("issue")
            or finding.get("type")
            or str(finding)
        )

        severity_value = str(
            finding.get("severity", "medium")
        ).lower()

        line = (
            finding.get("line")
            or finding.get("line_number")
            or 1
        )

        title = (
            finding.get("type")
            or default_title
        )

    else:
        message = str(finding)
        severity_value = "medium"
        line = 1
        title = default_title

    severity = _SEVERITY_MAP.get(
        severity_value,
        Severity.MEDIUM,
    )

    try:
        line_number = max(1, int(line))
    except (TypeError, ValueError):
        line_number = 1

    return Finding(
        rule_id=(
            rule_id
            if index == 0
            else f"{rule_id}-{index + 1:03d}"
        ),
        title=str(title),
        description=str(message),
        severity=severity,
        location=SourceLocation(
            file_path=context.file_path,
            line_start=line_number,
            line_end=line_number,
        ),
        analyzer=analyzer,
        confidence=1.0,
    )


def convert_legacy_findings(
    findings: list[Any],
    context: AnalysisContext,
    *,
    rule_id: str,
    analyzer: str,
    default_title: str,
) -> list[Finding]:
    return [
        convert_legacy_finding(
            finding,
            context,
            rule_id=rule_id,
            analyzer=analyzer,
            index=index,
            default_title=default_title,
        )
        for index, finding in enumerate(findings)
    ]
