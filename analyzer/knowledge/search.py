from __future__ import annotations

from dataclasses import dataclass

from analyzer.knowledge.models import RepositoryKnowledgeModel


@dataclass(frozen=True, slots=True)
class KnowledgeSearchResult:
    kind: str
    identifier: str
    file_path: str
    name: str
    score: float


def search_repository(
    knowledge: RepositoryKnowledgeModel,
    query: str,
    *,
    limit: int = 20,
) -> tuple[KnowledgeSearchResult, ...]:
    if limit <= 0:
        return ()

    terms = tuple(
        term
        for term in query.strip().lower().split()
        if term
    )

    if not terms:
        return ()

    results: list[KnowledgeSearchResult] = []

    for symbol in knowledge.symbols:
        name = symbol.name.lower()
        kind = symbol.kind.lower()
        file_path = symbol.file_path.lower()
        symbol_id = symbol.symbol_id.lower()

        haystack = " ".join(
            (
                name,
                kind,
                file_path,
                symbol_id,
            )
        )

        matched_terms = sum(
            term in haystack
            for term in terms
        )

        if matched_terms == 0:
            continue

        score = float(matched_terms)

        if all(term in name for term in terms):
            score += 3.0

        elif any(term in name for term in terms):
            score += 1.0

        if all(term in file_path for term in terms):
            score += 1.0

        results.append(
            KnowledgeSearchResult(
                kind=symbol.kind,
                identifier=symbol.symbol_id,
                file_path=symbol.file_path,
                name=symbol.name,
                score=score,
            )
        )

    results.sort(
        key=lambda result: (
            -result.score,
            result.file_path,
            result.name,
            result.identifier,
        )
    )

    return tuple(results[:limit])
