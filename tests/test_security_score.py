from analyzer.security_score import (
    calculate_security_score
)

findings = [

    {
        "severity": "Critical"
    },

    {
        "severity": "Critical"
    },

    {
        "severity": "Critical"
    }

]

print(
    calculate_security_score(
        findings
    )
)
