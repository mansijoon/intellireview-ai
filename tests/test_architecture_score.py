from analyzer.architecture_score import (
    calculate_architecture_score,
)


def test_architecture_score_accounts_for_issue_ratio():
    findings = [
        {
            "type": "God Module",
        },
        {
            "type": "Large Module",
        },
    ]

    score = calculate_architecture_score(
        findings,
        total_modules=10,
    )

    assert score == 94


def test_architecture_score_is_perfect_for_empty_repository():
    assert calculate_architecture_score(
        [],
        total_modules=0,
    ) == 100


def test_architecture_score_is_bounded():
    findings = [
        {
            "type": "God Module",
        }
        for _ in range(20)
    ]

    score = calculate_architecture_score(
        findings,
        total_modules=1,
    )

    assert score == 0
