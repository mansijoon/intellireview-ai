from analyzer.static_analysis import run_static_analysis
from analyzer.code_metrics import calculate_metrics


def calculate_technical_debt(code: str):
    """
    Calculates a technical debt score for a source file.

    Returns:
        {
            "score": int,
            "grade": str,
            "issues": int,
            "complexity": int,
            "loc": int
        }
    """

    findings = run_static_analysis(code)
    metrics = calculate_metrics(code)

    issue_count = len(findings)

    complexity = metrics.get(
        "cyclomatic_complexity",
        0
    )

    loc = metrics.get(
        "lines_of_code",
        0
    )

    score = 100

    score -= issue_count * 5
    score -= complexity * 2

    if loc > 500:
        score -= 10

    score = max(0, score)

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
        "issues": issue_count,
        "complexity": complexity,
        "loc": loc,
    }
