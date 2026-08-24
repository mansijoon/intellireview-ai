from collections import Counter


def calculate_architecture_score(findings, total_modules):
    """
    Calculate architecture score based on the proportion of architectural issues
    instead of raw counts, making the score scale fairly for repositories of
    different sizes.
    """

    if total_modules <= 0:
        return 100

    weights = {
        "God Module": 40,
        "Large Module": 25,
        "Large Repository": 10,
    }

    counts = Counter(f["type"] for f in findings)

    penalty = 0.0

    for finding_type, weight in weights.items():
        ratio = counts.get(finding_type, 0) / total_modules
        penalty += ratio * weight

    score = round(100 - penalty)

    return max(0, min(100, score))
