def summarize_security_findings(
    findings
):

    security_types = []

    critical = 0
    high = 0
    medium = 0
    low = 0

    security_keywords = [

        "Password",
        "Token",
        "Key",
        "URL",
        "Private"

    ]

    for finding in findings:

        finding_type = finding.get(
            "type",
            ""
        )

        if not any(
            keyword in finding_type
            for keyword in security_keywords
        ):
            continue

        severity = finding.get(
            "severity",
            "Low"
        )

        if severity == "Critical":

            critical += 1

        elif severity == "High":

            high += 1

        elif severity == "Medium":

            medium += 1

        else:

            low += 1

        security_types.append(
            finding_type
        )

    return {

        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,

        "types": sorted(
            set(
                security_types
            )
        )
    }
