from __future__ import annotations

from dataclasses import dataclass

from analyzer.knowledge.models import RepositoryKnowledgeModel
from analyzer.knowledge.search import (
    KnowledgeSearchResult,
    search_repository,
)


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
    results = search_repository(
        knowledge,
        query,
        limit=limit,
    )

    items: list[RepositoryContextItem] = []

    for result in results:
        content = ""

        try:
            with open(
                result.file_path,
                "r",
                encoding="utf-8",
            ) as handle:
                content = handle.read(
                    max_chars_per_file
                )
        except (
            OSError,
            UnicodeDecodeError,
        ):
            continue

        items.append(
            RepositoryContextItem(
                kind=result.kind,
                identifier=result.identifier,
                file_path=result.file_path,
                name=result.name,
                score=result.score,
                content=content,
            )
        )

    return RepositoryContextSelection(
        query=query,
        items=tuple(items),
    )
