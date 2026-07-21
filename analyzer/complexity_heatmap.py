import os

from analyzer.code_metrics import calculate_metrics


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


def generate_complexity_heatmap(repo_path):
    """
    Returns file complexity information sorted by complexity.
    """

    results = []

    for root, _, files in os.walk(repo_path):

        for file in files:

            if not file.endswith(SUPPORTED_EXTENSIONS):
                continue

            path = os.path.join(root, file)

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    code = f.read()

                metrics = calculate_metrics(code)

                results.append(
                    {
                        "file": os.path.relpath(
                            path,
                            repo_path
                        ),
                        "complexity": metrics.get(
                            "cyclomatic_complexity",
                            0
                        ),
                        "loc": metrics.get(
                            "lines_of_code",
                            0
                        ),
                    }
                )

            except Exception:
                continue

    results.sort(
        key=lambda x: x["complexity"],
        reverse=True
    )

    return results
