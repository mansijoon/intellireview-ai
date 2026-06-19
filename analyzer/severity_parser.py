import re

def extract_severity_counts(review):

    return {
        "Critical": len(
            re.findall(
                r"Severity:\s*Critical",
                review,
                re.IGNORECASE
            )
        ),
        "High": len(
            re.findall(
                r"Severity:\s*High",
                review,
                re.IGNORECASE
            )
        ),
        "Medium": len(
            re.findall(
                r"Severity:\s*Medium",
                review,
                re.IGNORECASE
            )
        ),
        "Low": len(
            re.findall(
                r"Severity:\s*Low",
                review,
                re.IGNORECASE
            )
        )
    }
