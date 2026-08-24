from analyzer.fix_suggester import (
    generate_fix_suggestions
)

findings = [
    {
        "type":"Unused Import",
        "severity":"Low"
    },
    {
        "type":"Hardcoded Password",
        "severity":"Critical"
    }
]

print(
    generate_fix_suggestions(
        findings
    )
)
