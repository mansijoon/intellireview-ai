import os

from analyzer.core.repository_loader import RepositoryLoader
from analyzer.knowledge.builder import build_repository_knowledge
from analyzer.knowledge.context import select_repository_context
from analyzer.knowledge.prompt_context import format_repository_context
from analyzer.review_engine import review_code


MAX_FILES_TO_REVIEW = 3


def review_repository(
    repo_path,
    repo_files,
):
    results = []

    # Build repository knowledge once.
    repository = RepositoryLoader().load(repo_path)
    knowledge = build_repository_knowledge(repository)

    for file in repo_files:
        if len(results) >= MAX_FILES_TO_REVIEW:
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
                ".ts",
            )
        ):
            continue

        full_path = os.path.join(repo_path, file)

        try:
            with open(
                full_path,
                "r",
                encoding="utf-8",
            ) as f:
                code = f.read()

            selection = select_repository_context(
                knowledge,
                (
                    "code review "
                    "security vulnerabilities "
                    "performance issues "
                    "architecture "
                    "maintainability "
                    "dependencies "
                    f"related to {file}"
                ),
            )

            repository_context = format_repository_context(
                selection
            )

            review = review_code(
                code,
                repository_context=repository_context,
            )

            results.append(
                {
                    "file": file,
                    "review": review,
                }
            )

        except Exception:
            continue

    return results
