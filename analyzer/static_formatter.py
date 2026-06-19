def format_static_findings(
    findings
):

    if not findings:

        return "No static analysis findings."

    lines = []

    for finding in findings:

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

        lines.append("")

    return "\n".join(lines)
