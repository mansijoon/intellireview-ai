def calculate_security_score(findings):

    score = 100

    for finding in findings:

        if finding["severity"] == "Critical":

            score -= 15

        elif finding["severity"] == "High":

            score -= 10

        elif finding["severity"] == "Medium":

            score -= 5

        else:

            score -= 2

    if score < 0:

        score = 0

    return score
