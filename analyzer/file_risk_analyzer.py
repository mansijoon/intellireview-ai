import os

from analyzer.code_metrics import (
    calculate_metrics
)


def analyze_repository_files(
    repo_path
):

    results = []

    for root, _, files in os.walk(
        repo_path
    ):

        for file in files:

            if file.endswith(
                (
                    ".py",
                    ".java",
                    ".cpp",
                    ".js"
                )
            ):

                path = os.path.join(
                    root,
                    file
                )

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        code = f.read()

                    metrics = calculate_metrics(
                        code
                    )

                    results.append(
                        {
                            "file": os.path.relpath(
                                path,
                                repo_path
                            ),
                            "lines": metrics["lines"],
                            "complexity": metrics["complexity_score"],
                            "risk": metrics["risk"]
                        }
                    )

                except Exception:

                    pass

    return sorted(
        results,
        key=lambda x: x["complexity"],
        reverse=True
    )
