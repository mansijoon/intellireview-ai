from __future__ import annotations

import json
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


SOURCE = Path.cwd()

# Small controlled corpus.
# No Gemini/API calls are made by this benchmark.
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


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="intellireview-context-benchmark-"
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

        # Full retrievable repository knowledge content.
        #
        # This deliberately measures only document content,
        # not metadata, because Metric #4 is about code context
        # supplied to retrieval/review.
        full_content_chars = sum(
            len(document.content)
            for document in documents
        )

        # Deterministic proxy for the retrieval layer:
        # rank documents by lexical overlap with the same type
        # of review query used by repository_reviewer.py.
        query = (
            "code review security vulnerabilities "
            "performance issues architecture "
            "maintainability dependencies"
        )

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

            # Prefer documents containing more query evidence.
            # Stable document_id ordering makes the benchmark
            # reproducible when scores tie.
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
                    scored[index][0]
                ),
                content=document.content[:12000],
            )
            for index, document in enumerate(
                selected_documents
            )
        )

        selection = RepositoryContextSelection(
            query=query,
            items=items,
        )

        formatted_context = format_repository_context(
            selection,
            max_total_chars=30000,
        )

        selected_context_chars = len(
            formatted_context
        )

        reduction_pct = (
            (
                1
                - (
                    selected_context_chars
                    / full_content_chars
                )
            )
            * 100
            if full_content_chars
            else 0.0
        )

        retained_pct = (
            (
                selected_context_chars
                / full_content_chars
            )
            * 100
            if full_content_chars
            else 0.0
        )

        result = {
            "benchmark": {
                "metric": "repository-context reduction",
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
                "query": query,
            },
            "full_available_context": {
                "characters": full_content_chars,
            },
            "selected_review_context": {
                "characters": selected_context_chars,
                "items": len(selection.items),
                "files": sorted(
                    {
                        item.file_path
                        for item in selection.items
                    }
                ),
            },
            "derived": {
                "context_reduction_pct": reduction_pct,
                "context_retained_pct": retained_pct,
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
