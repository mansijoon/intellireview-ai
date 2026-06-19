def generate_executive_summary(
    score,
    static_score,
    security_score,
    static_findings,
    severities
):

    summary = []

    summary.append(
        f"Code Quality Score: {score}/100"
    )

    summary.append(
        f"Static Analysis Score: {static_score}/100"
    )

    summary.append(
        f"Security Score: {security_score}/100"
    )

    summary.append("")

    summary.append(
        f"Critical Issues: {severities['Critical']}"
    )

    summary.append(
        f"High Issues: {severities['High']}"
    )

    summary.append(
        f"Medium Issues: {severities['Medium']}"
    )

    summary.append(
        f"Low Issues: {severities['Low']}"
    )

    summary.append("")

    summary.append(
        "Top Findings:"
    )

    for finding in static_findings[:5]:

        summary.append(
            f"- {finding['type']}"
        )

    return "\n".join(
        summary
    )
