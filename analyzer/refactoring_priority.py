def generate_refactoring_priority(
    module_risks,
    complexity_heatmap,
    technical_debt,
):
    """
    Generate a prioritized refactoring list by combining
    risk, complexity and technical debt.
    """

    complexity_lookup = {
        item["file"]: item["complexity"]
        for item in complexity_heatmap
    }

    debt_lookup = {
        item["file"]: item["score"]
        for item in technical_debt["files"]
    }

    priorities = []

    for module in module_risks:

        name = module["module"]

        complexity = complexity_lookup.get(
            name,
            0
        )

        debt_score = debt_lookup.get(
            name,
            100
        )

        priority_score = (
            module["risk_score"] +
            complexity +
            (100 - debt_score)
        )

        priorities.append(
            {
                "module": name,
                "priority_score": priority_score,
                "risk_score": module["risk_score"],
                "complexity": complexity,
                "technical_debt": debt_score,
            }
        )

    priorities.sort(
        key=lambda x: x["priority_score"],
        reverse=True
    )

    return priorities
