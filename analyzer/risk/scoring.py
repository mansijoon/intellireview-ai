from __future__ import annotations

from analyzer.architecture.models import ArchitectureViolation
from analyzer.dependency.models import DependencyGraph
from analyzer.impact.models import ChangeImpactGraph
from analyzer.symbol.models import SymbolGraph
from analyzer.call.models import CallGraph

from analyzer.risk.models import (
    ModuleRisk,
    RiskFactor,
    RepositoryRiskReport,
)


def _risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _architecture_counts(
    violations: tuple[ArchitectureViolation, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for violation in violations:
        module = violation.source_module

        if module is None:
            continue

        counts[module] = counts.get(module, 0) + 1

    return counts


def calculate_repository_risk(
    dependency_graph: DependencyGraph,
    symbol_graph: SymbolGraph,
    call_graph: CallGraph,
    architecture_violations: tuple[
        ArchitectureViolation, ...
    ] = (),
    impact_graph: ChangeImpactGraph | None = None,
) -> RepositoryRiskReport:
    """
    Calculate repository risk from existing repository-intelligence artifacts.

    The score is normalized to 0-100 and is deliberately structural:
    dependency coupling, architecture violations, change impact, and
    unresolved call relationships contribute to risk.
    """

    factors: list[RiskFactor] = []

    module_count = max(1, len(dependency_graph))

    cycle_count = 0
    high_coupling_count = 0

    for violation in architecture_violations:
        if violation.violation_type.value == "dependency_cycle":
            cycle_count += 1

        if violation.violation_type.value == "high_coupling":
            high_coupling_count += 1

    if cycle_count:
        factors.append(
            RiskFactor(
                category="architecture",
                score=min(100.0, cycle_count * 20.0),
                weight=0.30,
                reason=(
                    f"{cycle_count} dependency cycle(s) detected."
                ),
            )
        )

    if high_coupling_count:
        factors.append(
            RiskFactor(
                category="coupling",
                score=min(
                    100.0,
                    high_coupling_count
                    / module_count
                    * 100.0,
                ),
                weight=0.15,
                reason=(
                    f"{high_coupling_count} high-coupling "
                    "architecture violation(s)."
                ),
            )
        )

    architecture_violation_count = len(
        architecture_violations
    )

    if architecture_violation_count:
        factors.append(
            RiskFactor(
                category="architecture",
                score=min(
                    100.0,
                    architecture_violation_count
                    / module_count
                    * 100.0,
                ),
                weight=0.20,
                reason=(
                    f"{architecture_violation_count} architecture "
                    "violation(s) detected."
                ),
            )
        )

    unresolved_calls = call_graph.unresolved_call_count

    if call_graph.call_count:
        unresolved_ratio = (
            unresolved_calls
            / call_graph.call_count
            * 100.0
        )

        if unresolved_calls:
            factors.append(
                RiskFactor(
                    category="call_resolution",
                    score=unresolved_ratio,
                    weight=0.10,
                    reason=(
                        f"{unresolved_calls} of "
                        f"{call_graph.call_count} call(s) "
                        "remain unresolved."
                    ),
                )
            )

    if impact_graph is not None:
        impact_count = impact_graph.impact_count

        if impact_count:
            impact_score = min(
                100.0,
                impact_count / module_count * 100.0,
            )

            factors.append(
                RiskFactor(
                    category="change_impact",
                    score=impact_score,
                    weight=0.25,
                    reason=(
                        f"{impact_count} repository entities "
                        "are affected by the configured change set."
                    ),
                )
            )

    weighted_total = sum(
        factor.weighted_score
        for factor in factors
    )

    weight_total = sum(
        factor.weight
        for factor in factors
    )

    repository_score = (
        weighted_total / weight_total
        if weight_total
        else 0.0
    )

    architecture_counts = _architecture_counts(
        architecture_violations
    )

    impacted_modules: dict[str, int] = {}

    if impact_graph is not None:
        for target in impact_graph.impacted_modules:
            impacted_modules[target.target_id] = (
                impacted_modules.get(target.target_id, 0) + 1
            )

    module_risks: list[ModuleRisk] = []

    for module_name in sorted(
        dependency_graph.modules
    ):
        module = dependency_graph.modules[
            module_name
        ]

        module_factors: list[RiskFactor] = []

        dependency_score = min(
            100.0,
            (
                len(module.imports)
                + len(module.imported_by)
            )
            * 10.0,
        )

        if dependency_score:
            module_factors.append(
                RiskFactor(
                    category="coupling",
                    score=dependency_score,
                    weight=0.35,
                    reason=(
                        f"{len(module.imports)} outgoing and "
                        f"{len(module.imported_by)} incoming "
                        "internal dependencies."
                    ),
                    target=module_name,
                )
            )

        violation_score = min(
            100.0,
            architecture_counts.get(module_name, 0)
            * 25.0,
        )

        if violation_score:
            module_factors.append(
                RiskFactor(
                    category="architecture",
                    score=violation_score,
                    weight=0.25,
                    reason=(
                        f"{architecture_counts[module_name]} "
                        "architecture violation(s)."
                    ),
                    target=module_name,
                )
            )

        impact_score = min(
            100.0,
            impacted_modules.get(module_name, 0)
            * 25.0,
        )

        if impact_score:
            module_factors.append(
                RiskFactor(
                    category="change_impact",
                    score=impact_score,
                    weight=0.25,
                    reason=(
                        f"{impacted_modules[module_name]} "
                        "impact relationship(s)."
                    ),
                    target=module_name,
                )
            )

        symbol_count = sum(
            1
            for symbol in symbol_graph.symbols.values()
            if symbol.module == module_name
        )

        call_count = sum(
            1
            for call in call_graph.calls
            if (
                call.caller_symbol_id.startswith(
                    f"{module_name}:"
                )
                or call.caller_symbol_id == module_name
            )
        )

        module_risk = (
            sum(
                factor.weighted_score
                for factor in module_factors
            )
            / sum(
                factor.weight
                for factor in module_factors
            )
            if module_factors
            else 0.0
        )

        module_risks.append(
            ModuleRisk(
                module=module_name,
                risk_score=round(
                    min(100.0, module_risk),
                    2,
                ),
                risk_level=_risk_level(
                    module_risk
                ),
                dependency_count=len(
                    module.imports
                ),
                dependent_count=len(
                    module.imported_by
                ),
                architecture_violations=architecture_counts.get(
                    module_name,
                    0,
                ),
                impacted_count=impacted_modules.get(
                    module_name,
                    0,
                ),
                symbol_count=symbol_count,
                call_count=call_count,
                factors=tuple(
                    module_factors
                ),
            )
        )

    module_risks.sort(
        key=lambda item: (
            item.risk_score,
            item.module,
        ),
        reverse=True,
    )

    return RepositoryRiskReport(
        risk_score=round(
            min(100.0, repository_score),
            2,
        ),
        risk_level=_risk_level(
            repository_score
        ),
        factors=factors,
        module_risks=module_risks,
    )
