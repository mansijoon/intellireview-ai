def compare_versions(
    old_score,
    new_score
):

    difference = (
        new_score
        - old_score
    )

    if difference > 0:

        status = "Improved"

    elif difference < 0:

        status = "Declined"

    else:

        status = "Unchanged"

    return {
        "old_score": old_score,
        "new_score": new_score,
        "difference": difference,
        "status": status
    }
