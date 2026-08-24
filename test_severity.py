from analyzer.severity_parser import (
    extract_severity_counts
)

sample = """
Severity: Critical
Severity: High
Severity: Medium
Severity: Low
Severity: Low
"""

print(
    extract_severity_counts(
        sample
    )
)
