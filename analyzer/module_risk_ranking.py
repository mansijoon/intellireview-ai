from analyzer.dependency.models import DependencyGraph


def rank_modules(dependency_analysis, technical_debt):
    """
    Rank modules using dependency information and technical debt.
    """

    graph: DependencyGraph = dependency_analysis["graph"]

    rankings = []

    for module_name, module in graph.modules.items():

        debt_score = technical_debt.get(module_name, 0)

        risk_score = (
            len(module.imports) * 2
            + len(module.imported_by) * 3
            + len(module.external_imports)
            + debt_score
        )

        rankings.append({
            "module": module_name,
            "risk_score": risk_score,
            "technical_debt": debt_score,
            "imports": len(module.imports),
            "imported_by": len(module.imported_by),
            "external_imports": len(module.external_imports),
        })

    rankings.sort(
        key=lambda x: x["risk_score"],
        reverse=True
    )

    return rankings
