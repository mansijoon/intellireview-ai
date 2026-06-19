def generate_repository_ai_summary(
    review_results
):

    total_files = len(
        review_results
    )

    summary = f"""
Repository AI Summary

Files Reviewed: {total_files}

"""

    for result in review_results:

        summary += (
            f"\n\nFile: {result['file']}\n"
        )

        summary += (
            result["review"]
        )

        summary += "\n"

    return summary
