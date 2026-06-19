def calculate_repository_health(
    repo_stats,
    findings=None
):

    score = 100

    complexity_penalty = min(
        repo_stats["avg_complexity"] * 0.5,
        40
    )

    score -= complexity_penalty

    if repo_stats["functions"] > 500:
        score -= 10

    elif repo_stats["functions"] > 200:
        score -= 5

    if repo_stats["classes"] > 100:
        score -= 10

    elif repo_stats["classes"] > 50:
        score -= 5

    if repo_stats["imports"] > 300:
        score -= 5

    elif repo_stats["imports"] > 100:
        score -= 2

    if findings:

        for finding in findings:

            severity = finding.get(
                "severity",
                ""
            )

            if severity == "Critical":
                score -= 15

            elif severity == "High":
                score -= 10

            elif severity == "Medium":
                score -= 5

            elif severity == "Low":
                score -= 2

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return round(score)
