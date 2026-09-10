from __future__ import annotations

from dataclasses import dataclass

from analyzer.knowledge.models import (
    KnowledgeDocument,
    RepositoryKnowledgeModel,
)
from analyzer.knowledge.search import (
    KnowledgeSearchResult,
    search_repository,
)
from analyzer.knowledge.semantic_index import (
    SemanticIndex,
)


@dataclass(frozen=True, slots=True)
class HybridSearchResult:
    document_id: str
    kind: str
    name: str
    file_path: str
    content: str
    lexical_score: float
    semantic_score: float
    combined_score: float


def hybrid_search(
    knowledge: RepositoryKnowledgeModel,
    query: str,
    semantic_index: SemanticIndex,
    *,
    limit: int = 10,
    lexical_limit: int = 50,
    semantic_limit: int = 50,
    lexical_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> tuple[HybridSearchResult, ...]:
    if limit <= 0:
        return ()

    if lexical_weight < 0:
        raise ValueError(
            "lexical_weight must be non-negative"
        )

    if semantic_weight < 0:
        raise ValueError(
            "semantic_weight must be non-negative"
        )

    weight_total = (
        lexical_weight
        + semantic_weight
    )

    if weight_total <= 0:
        raise ValueError(
            "At least one search weight must be positive"
        )

    lexical_results = search_repository(
        knowledge,
        query,
        limit=lexical_limit,
    )

    semantic_results = semantic_index.search(
        query,
        limit=semantic_limit,
    )

    lexical_scores: dict[str, float] = {}
    documents: dict[str, KnowledgeDocument] = {}

    # Map lexical results onto every corresponding semantic document.
    #
    # A lexical result normally identifies a symbol. That symbol has:
    #
    #   symbol document:
    #       source_id == symbol_id
    #
    #   containing file document:
    #       file_path == symbol.file_path
    #
    # This lets lexical evidence contribute to both repository
    # representations without requiring either representation to be
    # preferred artificially.
    for result in lexical_results:
        lexical_key = (
            f"{result.kind}:"
            f"{result.identifier}"
        )

        lexical_scores[lexical_key] = result.score

        matching_documents = [
            document
            for document in semantic_index.documents
            if (
                (
                    document.source_id
                    == result.identifier
                )
                or (
                    document.kind == "file"
                    and document.file_path
                    == result.file_path
                )
            )
        ]

        for document in matching_documents:
            documents.setdefault(
                document.document_id,
                document,
            )

    # Add semantic-only candidates.
    for result in semantic_results:
        documents.setdefault(
            result.document.document_id,
            result.document,
        )

    semantic_scores: dict[str, float] = {
        result.document.document_id: result.score
        for result in semantic_results
    }

    max_lexical = max(
        lexical_scores.values(),
        default=0.0,
    )

    max_semantic = max(
        semantic_scores.values(),
        default=0.0,
    )

    combined_scores: dict[str, float] = {}

    for document in documents.values():
        lexical_score = 0.0

        # A document can receive lexical evidence from:
        #
        #   1. an exact symbol match
        #   2. a symbol whose containing file is this document
        #
        # Use the strongest applicable lexical score.
        for result in lexical_results:
            if (
                document.source_id
                == result.identifier
            ):
                lexical_score = max(
                    lexical_score,
                    result.score,
                )

            elif (
                document.kind == "file"
                and document.file_path
                == result.file_path
            ):
                lexical_score = max(
                    lexical_score,
                    result.score,
                )

        lexical_normalized = (
            lexical_score / max_lexical
            if max_lexical > 0
            else 0.0
        )

        semantic_score = semantic_scores.get(
            document.document_id,
            0.0,
        )

        semantic_normalized = (
            semantic_score / max_semantic
            if max_semantic > 0
            else 0.0
        )

        combined_scores[
            document.document_id
        ] = (
            lexical_weight * lexical_normalized
            + semantic_weight * semantic_normalized
        ) / weight_total

    ranked = sorted(
        documents.values(),
        key=lambda document: (
            -combined_scores.get(
                document.document_id,
                0.0,
            ),
            document.file_path,
            document.name,
            document.document_id,
        ),
    )

    results: list[HybridSearchResult] = []

    for document in ranked[:limit]:
        lexical_score = 0.0

        for result in lexical_results:
            if (
                document.source_id
                == result.identifier
            ):
                lexical_score = max(
                    lexical_score,
                    result.score,
                )

            elif (
                document.kind == "file"
                and document.file_path
                == result.file_path
            ):
                lexical_score = max(
                    lexical_score,
                    result.score,
                )

        results.append(
            HybridSearchResult(
                document_id=document.document_id,
                kind=document.kind,
                name=document.name,
                file_path=document.file_path,
                content=document.content,
                lexical_score=lexical_score,
                semantic_score=semantic_scores.get(
                    document.document_id,
                    0.0,
                ),
                combined_score=combined_scores.get(
                    document.document_id,
                    0.0,
                ),
            )
        )

    return tuple(results)
