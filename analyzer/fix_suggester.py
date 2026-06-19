FIXES = {

    "Unused Import":
    "Remove the unused import statement.",

    "Unused Variable":
    "Remove the variable or use it where intended.",

    "Too Many Parameters":
    "Group parameters into a class, object, or configuration structure.",

    "Duplicate Function":
    "Keep one implementation and remove duplicates.",

    "Dead Function":
    "Remove the function if it is no longer required.",

    "Long Function":
    "Split the function into smaller focused functions.",

    "Deep Nesting":
    "Use guard clauses and helper functions to reduce nesting.",

    "Hardcoded Password":
    "Move credentials to environment variables or a secrets manager."
}


def generate_fix_suggestions(
    findings
):

    suggestions = []

    for finding in findings:

        issue_type = finding.get(
            "type",
            ""
        )

        if issue_type in FIXES:

            suggestions.append(
                {
                    "issue": issue_type,
                    "severity": finding.get(
                        "severity",
                        "Unknown"
                    ),
                    "fix": FIXES[issue_type]
                }
            )

    return suggestions
