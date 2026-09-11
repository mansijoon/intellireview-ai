import re


def _review_text(review):
    """Return legacy text representation when available."""
    if isinstance(review, str):
        return review

    if isinstance(review, dict):
        structured = review.get("review")

        if isinstance(structured, str):
            return structured

        if structured is not None:
            return getattr(structured, "verdict", "") or ""

    return ""


def extract_score(review):
    if isinstance(review, dict):
        structured = review.get("review")

        if structured is not None:
            score = getattr(structured, "quality_score", None)

            if score is not None:
                return int(score)

    match = re.search(
        r"(\d+)\s*/\s*100",
        _review_text(review),
    )

    if match:
        return int(match.group(1))

    return None


def extract_security(review):
    text = _review_text(review)

    match = re.search(
        r"Security Vulnerabilities.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(0).strip()

    return "No security issues detected."


def extract_performance(review):
    text = _review_text(review)

    match = re.search(
        r"Performance Issues.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(0).strip()

    return "No performance issues detected."


def extract_code_smells(review):
    text = _review_text(review)

    match = re.search(
        r"Code Smells?.*?(?=####\s*\d+\.|### Repository Readiness Assessment|### Overall Code Quality Score)",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(0).strip()

    return "No code smells detected."
