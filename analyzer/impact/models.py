from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from analyzer.core.models import SourceLocation


class ImpactType(StrEnum):
    """Classification of a change-impact relationship."""

    MODULE = "module"
    SYMBOL = "symbol"
    CALL = "call"


class ImpactDepth(StrEnum):
    """Distance from the explicitly changed target."""

    DIRECT = "direct"
    TRANSITIVE = "transitive"


@dataclass(frozen=True, slots=True)
class ImpactTarget:
    """A repository entity affected by a change."""

    target_id: str
    impact_type: ImpactType
    depth: ImpactDepth
    location: SourceLocation | None = None
    source_id: str | None = None
    reason: str = ""


@dataclass(slots=True)
class ChangeImpactGraph:
    """Repository-wide change-impact relationships."""

    changed_targets: tuple[str, ...] = field(
        default_factory=tuple
    )

    impacted_modules: list[ImpactTarget] = field(
        default_factory=list
    )

    impacted_symbols: list[ImpactTarget] = field(
        default_factory=list
    )

    impacted_calls: list[ImpactTarget] = field(
        default_factory=list
    )

    @property
    def direct_impact_count(self) -> int:
        return sum(
            target.depth == ImpactDepth.DIRECT
            for target in (
                self.impacted_modules
                + self.impacted_symbols
                + self.impacted_calls
            )
        )

    @property
    def transitive_impact_count(self) -> int:
        return sum(
            target.depth == ImpactDepth.TRANSITIVE
            for target in (
                self.impacted_modules
                + self.impacted_symbols
                + self.impacted_calls
            )
        )

    @property
    def impact_count(self) -> int:
        return (
            self.direct_impact_count
            + self.transitive_impact_count
        )
