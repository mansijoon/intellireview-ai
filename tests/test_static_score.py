from analyzer.static_score import (
    calculate_static_score
)

findings = [

    {
        "severity": "Critical"
    },

    {
        "severity": "Medium"
    },

    {
        "severity": "Medium"
    }

]

print(
    calculate_static_score(
        findings
    )
)
