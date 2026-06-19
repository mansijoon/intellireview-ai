def calculate_static_score(findings):

    score = 100

    penalties = {

        "Critical": 20,
        "High": 10,
        "Medium": 5,
        "Low": 2

    }

    for finding in findings:

        severity = finding.get(
            "severity",
            "Low"
        )

        score -= penalties.get(
            severity,
            0
        )

    if score < 0:

        score = 0

    return score
