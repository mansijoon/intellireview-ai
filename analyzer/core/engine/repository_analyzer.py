from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from analyzer.core.repository_context import RepositoryContext


class RepositoryAnalyzer(ABC):
    """
    Contract for analyzers that require repository-wide context.

    Repository analyzers operate after repository loading and may
    produce derived artifacts stored on RepositoryContext.
    """

    @property
    @abstractmethod
    def analyzer_id(self) -> str:
        """Stable identifier for this repository analyzer."""

    @abstractmethod
    def analyze(
        self,
        repository: RepositoryContext,
    ) -> Any:
        """
        Analyze the repository and return an analyzer-specific result.
        """
        raise NotImplementedError
