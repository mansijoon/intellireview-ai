import os

from analyzer.review_engine import (
    review_code
)

MAX_FILES_TO_REVIEW = 3


def review_repository(
    repo_path,
    repo_files
):

    results = []

    files_reviewed = 0

    for file in repo_files:

        if files_reviewed >= MAX_FILES_TO_REVIEW:
            break

        if not file.lower().endswith(
            (
                ".py",
                ".js",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".ts"
            )
        ):
            continue

        full_path = os.path.join(
            repo_path,
            file
        )

        try:

            with open(
                full_path,
                "r",
                encoding="utf-8"
            ) as f:

                code = f.read()

            review = review_code(
                code
            )

            results.append(
                {
                    "file": file,
                    "review": review
                }
            )

            files_reviewed += 1

        except Exception:

            continue

    return results
