from analyzer.repository_executive_summary import (
    generate_repository_executive_summary
)

print(
    generate_repository_executive_summary(
        ["a.py", "b.py"],
        [
            {
                "severity":"Critical"
            },
            {
                "severity":"Medium"
            }
        ],
        75,
        [
            {
                "file":"a.py",
                "risk_score":22
            },
            {
                "file":"b.py",
                "risk_score":2
            }
        ]
    )
)
