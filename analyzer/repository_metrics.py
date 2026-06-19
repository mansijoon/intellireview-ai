import os

from analyzer.code_metrics import (
    calculate_metrics
)


SUPPORTED_EXTENSIONS = (
    ".py",
    ".java",
    ".cpp",
    ".js"
)


def repository_metrics(
    repo_path
):

    total_lines = 0
    total_functions = 0
    total_classes = 0
    total_imports = 0
    total_complexity = 0
    file_count = 0

    for root, dirs, files in os.walk(
        repo_path
    ):

        for file in files:

            if file.endswith(
                SUPPORTED_EXTENSIONS
            ):

                file_path = os.path.join(
                    root,
                    file
                )

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        code = f.read()

                    metrics = calculate_metrics(
                        code
                    )

                    total_lines += metrics["lines"]
                    total_functions += metrics["functions"]
                    total_classes += metrics["classes"]
                    total_imports += metrics["imports"]
                    total_complexity += metrics["complexity_score"]

                    file_count += 1

                except Exception:
                    pass

    avg_complexity = 0

    if file_count > 0:

        avg_complexity = round(
            total_complexity / file_count,
            2
        )

    return {
        "files": file_count,
        "lines": total_lines,
        "functions": total_functions,
        "classes": total_classes,
        "imports": total_imports,
        "avg_complexity": avg_complexity
    }


