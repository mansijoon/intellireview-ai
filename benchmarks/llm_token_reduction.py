from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from analyzer.core.repository_loader import RepositoryLoader
from analyzer.knowledge.builder import build_repository_knowledge
from analyzer.knowledge.documents import build_knowledge_documents
from analyzer.knowledge.context import (
    RepositoryContextItem,
    RepositoryContextSelection,
)
from analyzer.knowledge.prompt_context import format_repository_context
from analyzer.prompts import REVIEW_PROMPT


SOURCE = Path.cwd()
MAX_SOURCE_FILES = 12


def copy_repo(destination: Path) -> None:
    shutil.copytree(
        SOURCE,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            "venv",
            ".intellireview-cache",
            "__pycache__",
            ".pytest_cache",
            "build",
            "dist",
            "*.egg-info",
            "uploads",
            "reports",
        ),
        dirs_exist_ok=True,
    )


def estimate_tokens(text: str) -> int:
    """
    Deterministic GPT-style approximation.

    Approximation:
    - words / identifiers / punctuation are split into token-like units
    - long identifiers are split into smaller subword-like chunks
    """
    if not text:
        return 0

    pieces = re.findall(
        r"[A-Za-z]+|\d+|[^A-Za-z0-9\s]",
        text,
    )

    tokens = 0

    for piece in pieces:
        if piece.isdigit():
            tokens += max(1, (len(piece) + 2) // 3)
        elif piece.isalpha():
            tokens += max(1, (len(piece) + 3) // 4)
        else:
            tokens += 1

    return tokens


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="intellireview-token-benchmark-"
    ) as tmp:
        root = Path(tmp) / "repo"
        copy_repo(root)

        python_files = sorted(
            p
            for p in root.rglob("*.py")
            if "benchmarks" not in p.parts
            and "__pycache__" not in p.parts
        )

        selected = python_files[:MAX_SOURCE_FILES]
        selected_rel = {
            p.relative_to(root)
            for p in selected
        }

        for path in python_files:
            if path.relative_to(root) not in selected_rel:
                path.unlink()

        repository = RepositoryLoader().load(str(root))
        knowledge = build_repository_knowledge(repository)
        documents = build_knowledge_documents(knowledge)

        if not documents:
            raise SystemExit(
                "No knowledge documents were generated."
            )

        # Target file/code.
        target = selected[0]
        target_relative = str(
            target.relative_to(root)
        )

        code = target.read_text(
            encoding="utf-8"
        )

        query = (
            "code review security vulnerabilities "
            "performance issues architecture "
            "maintainability dependencies"
        )

        # Full repository knowledge content.
        full_repository_context = "\n\n".join(
            document.content
            for document in documents
        )

        # Deterministic retrieval proxy.
        query_terms = {
            term.lower()
            for term in query.split()
            if len(term) >= 4
        }

        scored = []

        for document in documents:
            content_lower = document.content.lower()

            score = sum(
                content_lower.count(term)
                for term in query_terms
            )

            scored.append(
                (
                    score,
                    document.document_id,
                    document,
                )
            )

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_documents = [
            item[2]
            for item in scored[:10]
            if item[0] > 0
        ]

        items = tuple(
            RepositoryContextItem(
                kind=document.kind,
                identifier=(
                    document.source_id
                    or document.document_id
                ),
                file_path=document.file_path,
                name=document.name,
                score=float(
                    next(
                        score
                        for score, doc_id, _ in scored
                        if doc_id == document.document_id
                    )
                ),
                content=document.content[:12000],
            )
            for document in selected_documents
        )

        selection = RepositoryContextSelection(
            query=query,
            items=items,
        )

        selected_repository_context = (
            format_repository_context(
                selection,
                max_total_chars=30000,
            )
        )

        # Construct prompts using the production REVIEW_PROMPT
        # structure. We deliberately do NOT call the model.
        baseline_prompt = REVIEW_PROMPT.format(
            code=code,
            language=target.suffix.lstrip("."),
        )

        final_prompt = REVIEW_PROMPT.format(
            code=code,
            language=target.suffix.lstrip("."),
        )

        final_prompt += f"""
Repository context:
{selected_repository_context}
"""

        # A second comparison isolates the repository-context
        # contribution itself.
        baseline_tokens = estimate_tokens(
            baseline_prompt
        )

        final_tokens = estimate_tokens(
            final_prompt
        )

        repository_context_tokens = estimate_tokens(
            full_repository_context
        )

        selected_context_tokens = estimate_tokens(
            selected_repository_context
        )

        token_reduction_pct = (
            (
                1
                - (
                    selected_context_tokens
                    / repository_context_tokens
                )
            )
            * 100
            if repository_context_tokens
            else 0.0
        )

        total_prompt_change_pct = (
            (
                1
                - (
                    final_tokens
                    / (
                        baseline_tokens
                        + repository_context_tokens
                    )
                )
            )
            * 100
            if (
                baseline_tokens
                + repository_context_tokens
            )
            else 0.0
        )

        result = {
            "benchmark": {
                "metric": "LLM token reduction",
                "corpus": (
                    "controlled subset of actual "
                    "IntelliReview repository"
                ),
                "source_files": len(selected),
                "knowledge_documents": len(documents),
                "retrieval_limit": 10,
                "max_chars_per_file": 12000,
                "max_total_context_chars": 30000,
                "api_calls": 0,
                "tokenizer": (
                    "deterministic GPT-style "
                    "token approximation"
                ),
            },
            "repository_context": {
                "baseline_estimated_tokens": (
                    repository_context_tokens
                ),
                "selected_estimated_tokens": (
                    selected_context_tokens
                ),
            },
            "review_prompt": {
                "code_only_estimated_tokens": (
                    baseline_tokens
                ),
                "code_plus_full_repository_context_estimated_tokens": (
                    baseline_tokens
                    + repository_context_tokens
                ),
                "code_plus_selected_context_estimated_tokens": (
                    final_tokens
                ),
            },
            "derived": {
                "repository_context_token_reduction_pct": (
                    token_reduction_pct
                ),
                "estimated_tokens_removed": (
                    repository_context_tokens
                    - selected_context_tokens
                ),
                "selected_context_token_retention_pct": (
                    (
                        selected_context_tokens
                        / repository_context_tokens
                    )
                    * 100
                    if repository_context_tokens
                    else 0.0
                ),
            },
            "selected_context": {
                "items": len(selection.items),
                "files": sorted(
                    {
                        item.file_path
                        for item in selection.items
                    }
                ),
            },
        }

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
