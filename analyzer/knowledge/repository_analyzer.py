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
from analyzer.knowledge.semantic_index import (
    SemanticIndex,
)


class KnowledgeRepositoryAnalyzer(RepositoryAnalyzer):
    """Build the canonical repository knowledge model."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="knowledge",
            depends_on=frozenset({"dependency", "symbol", "call"}),
        source_sensitive=False,
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

            semantic_index = SemanticIndex()

            if not semantic_index.ensure(
                knowledge
            ):
                raise RuntimeError(
                    "Unable to build semantic repository index"
                )

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts={
                    "knowledge_model": knowledge,
                    "semantic_index": semantic_index,
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
                    "semantic_document_count": len(
                        semantic_index.documents
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

            repository.set_artifact(
                "semantic_index",
                semantic_index,
            )

            return result

        except Exception as exc:
            diagnostic = AnalysisDiagnostic(
                message=(
                    "Knowledge analyzer execution failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
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
