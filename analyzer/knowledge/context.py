from __future__ import annotations

from dataclasses import dataclass

from analyzer.knowledge.hybrid_search import hybrid_search
from analyzer.knowledge.models import RepositoryKnowledgeModel
from analyzer.knowledge.semantic_index import SemanticIndex


@dataclass(frozen=True, slots=True)
class RepositoryContextItem:
    kind: str
    identifier: str
    file_path: str
    name: str
    score: float
    content: str


@dataclass(frozen=True, slots=True)
class RepositoryContextSelection:
    query: str
    items: tuple[RepositoryContextItem, ...]


def select_repository_context(
    knowledge: RepositoryKnowledgeModel,
    query: str,
    *,
    limit: int = 10,
    max_chars_per_file: int = 12000,
) -> RepositoryContextSelection:
    if limit <= 0:
        return RepositoryContextSelection(
            query=query,
            items=(),
        )

    semantic_index = SemanticIndex()

    if not semantic_index.ensure(knowledge):
        return RepositoryContextSelection(
            query=query,
            items=(),
        )

    results = hybrid_search(
        knowledge,
        query,
        semantic_index,
        limit=limit,
    )

    items: list[RepositoryContextItem] = []

    for result in results:
        if result.kind == "file":
            content = knowledge.source_contents.get(
                result.file_path,
                "",
            )
        else:
            content = result.content

        if not content:
            continue

        content = content[:max_chars_per_file]

        items.append(
            RepositoryContextItem(
                kind=result.kind,
                identifier=result.document_id,
                file_path=result.file_path,
                name=result.name,
                score=result.combined_score,
                content=content,
            )
        )

    return RepositoryContextSelection(
        query=query,
        items=tuple(items),
    )
