from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from analyzer.core.analyzer_registry import (
    RepositoryAnalyzerRegistry,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    Finding,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.cache import (
    AnalyzerInvalidator,
    DependencyInvalidator,
    RepositoryAnalysisCache,
)


@dataclass(slots=True)
class RepositoryAnalysisRun:
    """Canonical result of one repository analysis run."""

    repository_id: str
    revision: str
    started_at: datetime
    completed_at: datetime

    results: tuple[RepositoryAnalysisResult, ...]

    @property
    def analyzer_count(self) -> int:
        return len(self.results)

    @property
    def failed_count(self) -> int:
        return sum(
            result.status == RepositoryAnalysisStatus.FAILED
            for result in self.results
        )

    @property
    def partial_count(self) -> int:
        return sum(
            result.status == RepositoryAnalysisStatus.PARTIAL
            for result in self.results
        )

    @property
    def successful_count(self) -> int:
        return sum(
            result.status == RepositoryAnalysisStatus.SUCCESS
            for result in self.results
        )

    @property
    def duration_ms(self) -> float:
        return (
            self.completed_at - self.started_at
        ).total_seconds() * 1000

    @property
    def status(self) -> RepositoryAnalysisStatus:
        """
        Determine the overall repository-analysis status.

        FAILED:
            At least one analyzer failed and none produced a partial
            result.

        PARTIAL:
            At least one analyzer failed or partially completed, while
            at least one analyzer completed successfully.

        SUCCESS:
            Every analyzer completed successfully.
        """

        if self.failed_count == self.analyzer_count:
            return RepositoryAnalysisStatus.FAILED

        if self.failed_count > 0 or self.partial_count > 0:
            return RepositoryAnalysisStatus.PARTIAL

        return RepositoryAnalysisStatus.SUCCESS

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Return all findings emitted by repository analyzers."""

        findings: list[Finding] = []

        for result in self.results:
            value = result.artifacts.get("findings")

            if value is None:
                continue

            if isinstance(value, Finding):
                findings.append(value)
                continue

            if isinstance(value, (list, tuple)):
                findings.extend(
                    finding
                    for finding in value
                    if isinstance(finding, Finding)
                )

        return tuple(findings)

    @property
    def diagnostics(self) -> tuple[AnalysisDiagnostic, ...]:
        """Return diagnostics from all analyzers."""

        diagnostics: list[AnalysisDiagnostic] = []

        for result in self.results:
            diagnostics.extend(result.diagnostics)

        return tuple(diagnostics)

    @property
    def artifacts(self) -> dict[str, Any]:
        """
        Return all analyzer artifacts using analyzer-scoped keys.

        Example:
            dependency.dependency_graph
            architecture.architecture_score
        """

        aggregated: dict[str, Any] = {}

        for result in self.results:
            prefix = result.analyzer_id

            for key, value in result.artifacts.items():
                aggregated[
                    f"{prefix}.{key}"
                ] = value

        return aggregated

    @property
    def analyzer_durations_ms(self) -> dict[str, float]:
        """Return execution duration for each analyzer."""

        return {
            result.analyzer_id: result.duration_ms
            for result in self.results
        }


class RepositoryAnalysisOrchestrator:
    """Runs registered repository analyzers."""

    def __init__(
        self,
        registry: RepositoryAnalyzerRegistry,
        *,
        cache: RepositoryAnalysisCache | None = None,
    ) -> None:
        self.registry = registry
        self.cache = cache

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisRun:
        started_at = datetime.now(timezone.utc)

        results: list[RepositoryAnalysisResult] = []

        previous_snapshot = None

        if self.cache is not None:
            previous_snapshot = self.cache.load_snapshot()

        change_set = None
        invalidated_analyzers = None

        if (
            self.cache is not None
            and previous_snapshot is not None
        ):
            change_set = self.cache.change_set(
                previous_snapshot,
                repository,
            )

            invalidated_analyzers = (
                AnalyzerInvalidator(self.registry)
                .invalidated_analyzers(change_set)
            )

            analysis_scope = set(
                change_set.changed
            )

            previous_dependency_result = (
                self.cache.get_latest("dependency")
            )

            previous_dependency_graph = None

            if previous_dependency_result is not None:
                previous_dependency_graph = (
                    previous_dependency_result.artifacts.get(
                        "dependency_graph"
                    )
                )

            if previous_dependency_graph is not None:
                affected_modules = (
                    DependencyInvalidator()
                    .affected_modules(
                        previous_dependency_graph,
                        change_set.changed,
                    )
                )

                module_paths = {
                    module.path
                    for module in (
                        previous_dependency_graph.modules.values()
                    )
                    if module.name in affected_modules
                }

                analysis_scope.update(module_paths)

            repository.configuration[
                "_intellireview_analysis_scope"
            ] = frozenset(analysis_scope)

        if self.cache is not None:
            repository.configuration[
                "_intellireview_analysis_cache"
            ] = self.cache

        for analyzer in self.registry.create_analyzers():
            analyzer_id = analyzer.metadata.analyzer_id

            cached_result = None

            should_recompute = (
                self.cache is None
                or previous_snapshot is None
                or invalidated_analyzers is None
                or analyzer_id in invalidated_analyzers
            )

            if not should_recompute:
                cached_result = self.cache.get_latest(
                    analyzer_id,
                )

            if cached_result is not None:
                results.append(cached_result)
                continue

            analyzer_started_at = datetime.now(timezone.utc)

            try:
                result = analyzer.analyze(
                    repository
                )

            except Exception as exc:
                completed_at = datetime.now(timezone.utc)

                result = RepositoryAnalysisResult(
                    analyzer_id=(
                        analyzer.metadata.analyzer_id
                    ),
                    status=RepositoryAnalysisStatus.FAILED,
                    started_at=analyzer_started_at,
                    completed_at=completed_at,
                    diagnostics=(
                        AnalysisDiagnostic(
                            message=(
                                "Analyzer execution failed: "
                                f"{exc}"
                            ),
                            severity="error",
                        ),
                    ),
                )

            results.append(result)

            if self.cache is not None:
                self.cache.set(
                    repository,
                    result,
                )

        if self.cache is not None:
            self.cache.save_snapshot(repository)

        completed_at = datetime.now(timezone.utc)

        return RepositoryAnalysisRun(
            repository_id=repository.repository_id,
            revision=repository.revision,
            started_at=started_at,
            completed_at=completed_at,
            results=tuple(results),
        )
