from __future__ import annotations

from analyzer.knowledge.models import (
    KnowledgeDocument,
    RepositoryKnowledgeModel,
)


def _symbol_content(
    knowledge: RepositoryKnowledgeModel,
    file_path: str,
    line_start: int,
    line_end: int | None,
) -> str:
    source = knowledge.source_contents.get(
        file_path,
        "",
    )

    if not source:
        return ""

    lines = source.splitlines()

    start = max(
        line_start - 1,
        0,
    )

    if line_end is None:
        end = min(
            start + 80,
            len(lines),
        )
    else:
        end = min(
            line_end,
            len(lines),
        )

    return "\n".join(
        lines[start:end]
    )


def build_knowledge_documents(
    knowledge: RepositoryKnowledgeModel,
) -> tuple[KnowledgeDocument, ...]:
    documents: list[KnowledgeDocument] = []

    for file_info in knowledge.files:
        source = knowledge.source_contents.get(
            file_info.file_path,
            "",
        )

        if not source:
            continue

        documents.append(
            KnowledgeDocument(
                document_id=f"file:{file_info.file_path}",
                kind="file",
                file_path=file_info.file_path,
                name=file_info.file_path,
                content=source,
            )
        )

    for symbol in knowledge.symbols:
        content = _symbol_content(
            knowledge,
            symbol.file_path,
            symbol.line_start,
            symbol.line_end,
        )

        if not content:
            continue

        documents.append(
            KnowledgeDocument(
                document_id=f"symbol:{symbol.symbol_id}",
                kind=symbol.kind,
                source_id=symbol.symbol_id,
                file_path=symbol.file_path,
                name=symbol.name,
                content=content,
                line_start=symbol.line_start,
                line_end=symbol.line_end,
            )
        )

    return tuple(
        documents
    )
