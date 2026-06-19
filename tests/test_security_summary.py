from analyzer.security_summary import (
    summarize_security_findings
)

findings = [

    {
        "type":"OpenAI API Key",
        "severity":"Critical"
    },

    {
        "type":"MongoDB URL",
        "severity":"Critical"
    }

]

print(
    summarize_security_findings(
        findings
    )
)
