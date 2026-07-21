from analyzer.file_risk_score import (
    calculate_file_risk
)

findings = [

    {
        "severity":"Critical"
    },

    {
        "severity":"Critical"
    },

    {
        "severity":"Medium"
    }

]

print(
    calculate_file_risk(
        findings
    )
)
