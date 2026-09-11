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

        review = result.get("review", "")

        if isinstance(review, dict):
            import json
            review = json.dumps(
                review,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        summary += str(review)

        summary += "\n"

    return summary
