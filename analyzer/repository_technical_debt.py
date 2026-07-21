import os

from analyzer.technical_debt import calculate_technical_debt


SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
)


def analyze_repository_technical_debt(repo_path):
    """
    Analyze technical debt across the repository.
    """

    files = []
    total_score = 0
    module_scores = {}

    for root, _, filenames in os.walk(repo_path):

        for filename in filenames:

            if not filename.endswith(SUPPORTED_EXTENSIONS):
                continue

            path = os.path.join(
                root,
                filename
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    code = f.read()

                debt = calculate_technical_debt(
                    code
                )

                debt["file"] = os.path.relpath(
                    path,
                    repo_path
                )

                files.append(
                    debt
                )

                total_score += debt["score"]

                module_name = os.path.splitext(
                    debt["file"]
                )[0].replace(
                    os.sep,
                    "."
                )

                # Higher value means more technical debt
                module_scores[module_name] = (
                    100 - debt["score"]
                )

            except Exception:
                continue

    average_score = (
        total_score / len(files)
        if files else 0
    )

    return {
        "average_score": round(
            average_score,
            2
        ),
        "files": sorted(
            files,
            key=lambda x: x["score"]
        ),
        "module_scores": module_scores
    }
