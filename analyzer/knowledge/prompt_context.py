from __future__ import annotations

from analyzer.knowledge.context import (
    RepositoryContextSelection,
)


def format_repository_context(
    context: RepositoryContextSelection,
    *,
    max_total_chars: int = 30000,
) -> str:
    if max_total_chars <= 0:
        return ""

    sections: list[str] = []
    total_chars = 0

    for item in context.items:
        section = (
            f"FILE: {item.file_path}\n"
            f"SYMBOL: {item.name}\n"
            f"KIND: {item.kind}\n"
            f"SCORE: {item.score:.2f}\n"
            f"CODE:\n"
            f"{item.content}\n"
        )

        remaining = (
            max_total_chars - total_chars
        )

        if remaining <= 0:
            break

        if len(section) > remaining:
            section = section[:remaining]

        sections.append(section)
        total_chars += len(section)

    return "\n---\n".join(sections)
