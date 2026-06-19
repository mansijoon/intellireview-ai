import os


def get_repository_files(path):

    files = []

    for root, dirs, filenames in os.walk(path):

        dirs[:] = [
            d for d in dirs
            if d not in (
                ".git",
                "__pycache__",
                "venv",
                "node_modules"
            )
        ]

        for file in filenames:

            if not file.lower().endswith(
                (
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                    ".hpp"
                )
            ):
                continue

            files.append(
                os.path.relpath(
                    os.path.join(root, file),
                    path
                )
            )

    return sorted(files)
