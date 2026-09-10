from __future__ import annotations

from analyzer.baseline.builder import build_baseline
from analyzer.baseline.comparator import compare_baseline
from analyzer.baseline.models import (
    Baseline,
    BaselineComparison,
)
from analyzer.baseline.store import BaselineStore
from analyzer.core.analyzer_defaults import create_default_analyzer_registry
from analyzer.core.repository_loader import RepositoryLoader
from analyzer.core.repository_orchestrator import (
    RepositoryAnalysisOrchestrator,
    RepositoryAnalysisRun,
)


def create_baseline(
    run: RepositoryAnalysisRun,
    repository_root: str,
) -> Baseline:
    baseline = build_baseline(run)

    BaselineStore(repository_root).save(baseline)

    return baseline


def load_baseline(
    repository_root: str,
) -> Baseline | None:
    return BaselineStore(repository_root).load()


def compare_current_run(
    run: RepositoryAnalysisRun,
    repository_root: str,
) -> BaselineComparison:
    baseline = load_baseline(repository_root)

    if baseline is None:
        raise FileNotFoundError(
            "No IntelliReview baseline exists for this repository."
        )

    current = build_baseline(run)

    return compare_baseline(
        baseline,
        current.findings,
        current_revision=run.revision,
    )


def compare_revisions(
    repository_root: str,
    *,
    from_revision: str,
    to_revision: str,
    repository_id: str | None = None,
) -> BaselineComparison:
    """Analyze and compare two explicit Git revisions."""

    if not from_revision.strip():
        raise ValueError("from_revision must not be empty")

    if not to_revision.strip():
        raise ValueError("to_revision must not be empty")

    loader = RepositoryLoader()
    registry = create_default_analyzer_registry()

    from_repository = loader.load(
        repository_root,
        repository_id=repository_id,
        revision=from_revision,
    )
    to_repository = loader.load(
        repository_root,
        repository_id=repository_id,
        revision=to_revision,
    )

    from_run = RepositoryAnalysisOrchestrator(registry).analyze(
        from_repository
    )
    to_run = RepositoryAnalysisOrchestrator(registry).analyze(
        to_repository
    )

    if from_run.status.value != "success":
        raise RuntimeError(
            f"Analysis failed for from revision: {from_run.revision}"
        )

    if to_run.status.value != "success":
        raise RuntimeError(
            f"Analysis failed for to revision: {to_run.revision}"
        )

    from_baseline = build_baseline(from_run)
    to_baseline = build_baseline(to_run)

    return compare_baseline(
        from_baseline,
        to_baseline.findings,
        current_revision=to_run.revision,
    )
