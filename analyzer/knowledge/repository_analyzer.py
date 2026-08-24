from __future__ import annotations

from datetime import datetime, timezone

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

from analyzer.knowledge.builder import (
    build_repository_knowledge,
)


class KnowledgeRepositoryAnalyzer(RepositoryAnalyzer):
    """Build the canonical repository knowledge model."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="knowledge",
        name="Repository Knowledge Analyzer",
        description=(
            "Builds the canonical repository knowledge model "
            "from repository files, dependency, symbol, and call graphs."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            knowledge = build_repository_knowledge(
                repository
            )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts={
                    "knowledge_model": knowledge,
                    "file_count": len(
                        knowledge.files
                    ),
                    "symbol_count": len(
                        knowledge.symbols
                    ),
                    "call_count": len(
                        knowledge.calls
                    ),
                    "resolved_call_count": (
                        knowledge.metadata[
                            "resolved_call_count"
                        ]
                    ),
                    "dependency_count": len(
                        knowledge.dependencies
                    ),
                },
                diagnostics=(),
            )

            repository.set_artifact(
                "knowledge_analysis",
                result,
            )

            repository.set_artifact(
                "repository_knowledge",
                knowledge,
            )

            return result

        except Exception as exc:
            diagnostic = AnalysisDiagnostic(
                code="KNOWLEDGE_ANALYSIS_ERROR",
                message=str(exc),
                severity="error",
            )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts={},
                diagnostics=(diagnostic,),
            )

            repository.set_artifact(
                "knowledge_analysis",
                result,
            )

            return result
