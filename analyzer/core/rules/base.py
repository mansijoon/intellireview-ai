from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from analyzer.core.context import AnalysisContext
from analyzer.core.models import Finding


@dataclass(frozen=True, slots=True)
class RuleMetadata:
    """Metadata describing an analysis rule."""

    rule_id: str
    name: str
    description: str
    category: str


class AnalysisRule(ABC):
    """Base contract for deterministic IntelliReview rules."""

    metadata: RuleMetadata

    @abstractmethod
    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        """Analyze a source file using shared analysis context."""
        raise NotImplementedError
