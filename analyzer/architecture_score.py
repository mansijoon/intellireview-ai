def calculate_architecture_score(
    findings
):

    score = 100

    penalties = {

        "God Module": 15,
        "Large Module": 5,
        "Large Repository": 3
    }

    for finding in findings:

        score -= penalties.get(
            finding["type"],
            0
        )

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return score
