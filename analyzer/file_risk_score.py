def calculate_file_risk(
    findings
):

    score = 0

    for finding in findings:

        severity = finding.get(
            "severity",
            "Low"
        )

        if severity == "Critical":

            score += 20

        elif severity == "High":

            score += 10

        elif severity == "Medium":

            score += 5

        else:

            score += 2

    return score
