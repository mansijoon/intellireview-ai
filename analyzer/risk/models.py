from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RiskFactor:
    """One measurable contributor to repository risk."""

    category: str
    score: float
    weight: float
    reason: str
    target: str | None = None

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass(frozen=True, slots=True)
class ModuleRisk:
    """Risk assessment for one repository module."""

    module: str
    risk_score: float
    risk_level: str
    dependency_count: int = 0
    dependent_count: int = 0
    architecture_violations: int = 0
    impacted_count: int = 0
    symbol_count: int = 0
    call_count: int = 0
    factors: tuple[RiskFactor, ...] = field(
        default_factory=tuple
    )


@dataclass(slots=True)
class RepositoryRiskReport:
    """Repository-wide risk assessment."""

    risk_score: float
    risk_level: str
    factors: list[RiskFactor] = field(
        default_factory=list
    )
    module_risks: list[ModuleRisk] = field(
        default_factory=list
    )

    @property
    def high_risk_modules(self) -> tuple[ModuleRisk, ...]:
        return tuple(
            module
            for module in self.module_risks
            if module.risk_level in {"high", "critical"}
        )
