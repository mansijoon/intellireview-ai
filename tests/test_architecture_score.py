from analyzer.architecture_score import (
    calculate_architecture_score
)

findings = [

    {
        "type": "God Module"
    },

    {
        "type": "Large Module"
    }
]

print(
    calculate_architecture_score(
        findings
    )
)
