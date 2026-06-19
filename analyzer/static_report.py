def format_static_findings(findings):

    if not findings:

        return "No static analysis findings."

    report = ""

    for finding in findings:

        report += (
            f"Type: {finding['type']}\n"
        )

        report += (
            f"Severity: {finding['severity']}\n"
        )

        if "message" in finding:

            report += (
                f"Message: {finding['message']}\n"
            )

        if "count" in finding:

            report += (
                f"Count: {finding['count']}\n"
            )

        report += "\n"

    return report
