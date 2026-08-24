from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from analyzer.core.analyzers import RepositoryAnalyzer


@dataclass(frozen=True, slots=True)
class RegisteredAnalyzer:
    """A repository analyzer registered with IntelliReview."""

    analyzer_class: Type[RepositoryAnalyzer]
    enabled: bool = True


class RepositoryAnalyzerRegistry:
    """Central registry for repository-wide analyzers."""

    def __init__(self) -> None:
        self._analyzers: dict[str, RegisteredAnalyzer] = {}

    def register(
        self,
        analyzer_class: Type[RepositoryAnalyzer],
        *,
        enabled: bool = True,
    ) -> None:
        analyzer_id = analyzer_class.metadata.analyzer_id

        if analyzer_id in self._analyzers:
            raise ValueError(
                f"Analyzer already registered: {analyzer_id}"
            )

        self._analyzers[analyzer_id] = RegisteredAnalyzer(
            analyzer_class=analyzer_class,
            enabled=enabled,
        )

    def unregister(
        self,
        analyzer_id: str,
    ) -> None:
        self._analyzers.pop(analyzer_id, None)

    def enable(
        self,
        analyzer_id: str,
    ) -> None:
        registered = self._get(analyzer_id)

        self._analyzers[analyzer_id] = RegisteredAnalyzer(
            analyzer_class=registered.analyzer_class,
            enabled=True,
        )

    def disable(
        self,
        analyzer_id: str,
    ) -> None:
        registered = self._get(analyzer_id)

        self._analyzers[analyzer_id] = RegisteredAnalyzer(
            analyzer_class=registered.analyzer_class,
            enabled=False,
        )

    def all(
        self,
    ) -> dict[str, RegisteredAnalyzer]:
        return dict(self._analyzers)

    def enabled(
        self,
    ) -> list[RepositoryAnalyzer]:
        return [
            registered.analyzer_class()
            for registered in self._analyzers.values()
            if registered.enabled
        ]

    def create_analyzers(
        self,
    ) -> list[RepositoryAnalyzer]:
        return self.enabled()

    def _get(
        self,
        analyzer_id: str,
    ) -> RegisteredAnalyzer:
        try:
            return self._analyzers[analyzer_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown analyzer: {analyzer_id}"
            ) from exc
