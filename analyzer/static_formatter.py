from __future__ import annotations

from analyzer.core.models import Finding


def format_static_findings(
    findings,
) -> str:
    if not findings:
        return "No static analysis findings."

    lines: list[str] = []

    for finding in findings:
        if isinstance(finding, Finding):
            lines.append(
                f"Rule: {finding.rule_id}"
            )
            lines.append(
                f"Type: {finding.title}"
            )
            lines.append(
                f"Severity: {finding.severity.value}"
            )
            lines.append(
                f"Message: {finding.description}"
            )
            lines.append(
                f"File: {finding.location.file_path}"
            )
            lines.append(
                f"Line: {finding.location.line_start}"
            )
            lines.append(
                f"Confidence: {finding.confidence}"
            )

        elif isinstance(finding, dict):
            lines.append(
                f"Type: {finding.get('type', 'Unknown')}"
            )
            lines.append(
                f"Severity: {finding.get('severity', 'Unknown')}"
            )

            if "message" in finding:
                lines.append(
                    f"Message: {finding['message']}"
                )

            if "count" in finding:
                lines.append(
                    f"Count: {finding['count']}"
                )

        else:
            lines.append(
                f"Type: {type(finding).__name__}"
            )
            lines.append(
                f"Message: {finding}"
            )

        lines.append("")

    return "\n".join(lines)
