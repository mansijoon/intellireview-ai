def generate_repository_executive_summary(
    repo_files,
    findings,
    health_score,
    risk_ranking
):

    critical = 0
    high = 0
    medium = 0
    low = 0

    for finding in findings:

        severity = finding.get(
            "severity",
            "Low"
        )

        if severity == "Critical":
            critical += 1

        elif severity == "High":
            high += 1

        elif severity == "Medium":
            medium += 1

        else:
            low += 1

    summary = []

    summary.append(
        f"Files Analyzed: {len(repo_files)}"
    )

    summary.append("")

    summary.append(
        f"Critical Findings: {critical}"
    )

    summary.append(
        f"High Findings: {high}"
    )

    summary.append(
        f"Medium Findings: {medium}"
    )

    summary.append(
        f"Low Findings: {low}"
    )

    summary.append("")

    summary.append(
        f"Repository Health Score: {health_score}/100"
    )

    summary.append("")

    summary.append(
        "Top Risk Files:"
    )

    for item in risk_ranking[:5]:

        summary.append(
            f"- {item['file']} ({item['risk_score']})"
        )

    return "\n".join(
        summary
    )
