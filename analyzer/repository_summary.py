def generate_repository_summary(
    repo_stats,
    file_count
):

    summary = f"""
Repository Summary

This repository contains {file_count} source files.

Statistics:
- Total Files: {repo_stats["files"]}
- Total Lines: {repo_stats["lines"]}
- Total Functions: {repo_stats["functions"]}
- Total Classes: {repo_stats["classes"]}
- Total Imports: {repo_stats["imports"]}

Assessment:

"""

    if repo_stats["avg_complexity"] > 15:

        summary += (
            "- High complexity detected. "
            "Consider refactoring large functions.\n"
        )

    else:

        summary += (
            "- Complexity appears manageable.\n"
        )

    if repo_stats["functions"] > 50:

        summary += (
            "- Large codebase with many functions.\n"
        )

    if repo_stats["classes"] > 20:

        summary += (
            "- Object-oriented structure detected.\n"
        )

    summary += (
        "\nOverall repository health appears reasonable. "
        "Further AI analysis is recommended."
    )

    return summary
