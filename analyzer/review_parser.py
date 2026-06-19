import re


def extract_score(review):

    match = re.search(
        r'(\d+)\s*/\s*100',
        review
    )

    if match:
        return int(match.group(1))

    return None


def extract_security(review):

    match = re.search(
        r"Security Vulnerabilities.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        review,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        return match.group(0).strip()

    return "No security issues detected."


def extract_performance(review):

    match = re.search(
        r"Performance Issues.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        review,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        return match.group(0).strip()

    return "No performance issues detected."


def extract_code_smells(review):

    match = re.search(
        r"Code Smells?.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        review,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        return match.group(0).strip()

    return "No code smells detected."
