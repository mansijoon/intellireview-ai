from __future__ import annotations

from analyzer.architecture import (
    ArchitectureValidationRepositoryAnalyzer,
)
from analyzer.architecture_repository_analyzer import (
    ArchitectureRepositoryAnalyzer,
)
from analyzer.call import CallRepositoryAnalyzer
from analyzer.core.analyzer_registry import (
    RepositoryAnalyzerRegistry,
)
from analyzer.dependency import DependencyRepositoryAnalyzer
from analyzer.impact import ChangeImpactRepositoryAnalyzer
from analyzer.risk import RepositoryRiskRepositoryAnalyzer
from analyzer.static import StaticRepositoryAnalyzer
from analyzer.complexity import ComplexityRepositoryAnalyzer
from analyzer.maintainability import MaintainabilityRepositoryAnalyzer
from analyzer.duplication import DuplicationRepositoryAnalyzer
from analyzer.dead_code import DeadCodeRepositoryAnalyzer
from analyzer.performance import PerformanceRepositoryAnalyzer
from analyzer.reliability import ReliabilityRepositoryAnalyzer
from analyzer.security import SecurityRepositoryAnalyzer
from analyzer.taint import TaintRepositoryAnalyzer
from analyzer.security.sbom import SBOMRepositoryAnalyzer
from analyzer.knowledge import KnowledgeRepositoryAnalyzer
from analyzer.symbol import SymbolRepositoryAnalyzer


def create_default_analyzer_registry() -> RepositoryAnalyzerRegistry:
    """Create the standard repository analyzer registry."""

    registry = RepositoryAnalyzerRegistry()

    registry.register(
        DependencyRepositoryAnalyzer
    )

    registry.register(
        ArchitectureRepositoryAnalyzer
    )

    registry.register(
        SymbolRepositoryAnalyzer
    )

    registry.register(
        CallRepositoryAnalyzer
    )

    registry.register(
        ArchitectureValidationRepositoryAnalyzer
    )

    registry.register(
        ChangeImpactRepositoryAnalyzer
    )

    registry.register(
        RepositoryRiskRepositoryAnalyzer
    )

    registry.register(
        StaticRepositoryAnalyzer
    )

    registry.register(
        ComplexityRepositoryAnalyzer
    )

    registry.register(
        MaintainabilityRepositoryAnalyzer
    )

    registry.register(
        DuplicationRepositoryAnalyzer
    )

    registry.register(
        DeadCodeRepositoryAnalyzer
    )

    registry.register(
        PerformanceRepositoryAnalyzer
    )

    registry.register(
        ReliabilityRepositoryAnalyzer
    )

    registry.register(
        SecurityRepositoryAnalyzer
    )

    registry.register(
        TaintRepositoryAnalyzer
    )
    registry.register(
        SBOMRepositoryAnalyzer
    )
    registry.register(
        KnowledgeRepositoryAnalyzer
    )

    return registry
