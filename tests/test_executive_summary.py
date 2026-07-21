from analyzer.executive_summary import (
    generate_executive_summary
)

print(
    generate_executive_summary(
        15,
        70,
        80,
        [
            {
                "type":"Hardcoded Password"
            },
            {
                "type":"Unused Import"
            }
        ],
        {
            "Critical":1,
            "High":0,
            "Medium":1,
            "Low":1
        }
    )
)
