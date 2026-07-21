from collections import Counter


def analyze_root_causes(repository_findings):
    """
    Groups repository findings into root causes.

    Returns:
        {
            "Duplicate Code": 8,
            "Unused Imports": 6,
            ...
        }
    """

    counter = Counter()

    for finding in repository_findings:

        issue = finding.get(
            "issue",
            "Unknown"
        )

        counter[issue] += 1

    return dict(
        counter.most_common()
    )
