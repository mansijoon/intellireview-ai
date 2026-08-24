from __future__ import annotations

from datetime import datetime, timezone

from analyzer.architecture.validator import validate_architecture
from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.dependency.builder import build_dependency_graph


class ArchitectureValidationRepositoryAnalyzer(
    RepositoryAnalyzer
):
    """Repository-wide deterministic architecture validation."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="architecture_validation",
        name="Architecture Validation Analyzer",
        description=(
            "Validates repository architecture using "
            "dependency relationships and configurable "
            "architectural constraints."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            dependency_graph = repository.get_artifact(
                "dependency_graph"
            )

            if dependency_graph is None:
                dependency_graph = build_dependency_graph(
                    repository
                )

                repository.set_artifact(
                    "dependency_graph",
                    dependency_graph,
                )

            forbidden_dependencies = (
                repository.configuration.get(
                    "architecture:forbidden_dependencies"
                )
            )

            coupling_threshold = (
                repository.configuration.get(
                    "architecture:coupling_threshold",
                    10,
                )
            )

            violations = validate_architecture(
                dependency_graph,
                forbidden_dependencies=(
                    forbidden_dependencies
                ),
                coupling_threshold=coupling_threshold,
            )

            finding_counts: dict[str, int] = {}

            for violation in violations:
                key = violation.violation_type.value
                finding_counts[key] = (
                    finding_counts.get(key, 0) + 1
                )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "architecture_violations": tuple(
                        violations
                    ),
                    "violation_count": len(
                        violations
                    ),
                    "finding_counts": finding_counts,
                    "dependency_graph": dependency_graph,
                },
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Architecture validation "
                            "completed successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Architecture validation "
                            f"failed: {exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "architecture_validation_analysis",
            result,
        )

        return result
