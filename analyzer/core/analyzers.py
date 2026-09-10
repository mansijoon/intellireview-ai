from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from analyzer.core.models import RepositoryAnalysisResult
from analyzer.core.repository_context import RepositoryContext


@dataclass(frozen=True, slots=True)
class RepositoryAnalyzerMetadata:
    """Metadata describing a repository-wide analyzer."""

    analyzer_id: str
    name: str
    description: str
    depends_on: frozenset[str] = frozenset()
    source_sensitive: bool = True

    def __post_init__(self) -> None:
        if not self.analyzer_id.strip():
            raise ValueError(
                "analyzer_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "name must not be empty"
            )

        if not self.description.strip():
            raise ValueError(
                "description must not be empty"
            )


class RepositoryAnalyzer(ABC):
    """Base contract for repository-wide analyzers."""

    metadata: RepositoryAnalyzerMetadata

    @abstractmethod
    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        """Analyze a repository and return a structured result."""

        raise NotImplementedError
