from __future__ import annotations

import hashlib
import os
from pathlib import Path

from analyzer.core.language import detect_language
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.models import SourceFile


DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "dist",
        "build",
        "uploads",
    }
)


class RepositoryLoader:
    """Build a RepositoryContext from a local repository."""

    def __init__(
        self,
        *,
        excluded_directories: frozenset[str] = (
            DEFAULT_EXCLUDED_DIRECTORIES
        ),
        max_file_size_bytes: int = 2 * 1024 * 1024,
    ) -> None:
        if max_file_size_bytes <= 0:
            raise ValueError(
                "max_file_size_bytes must be > 0"
            )

        self.excluded_directories = excluded_directories
        self.max_file_size_bytes = max_file_size_bytes

    def load(
        self,
        root_path: str,
        *,
        repository_id: str | None = None,
        revision: str = "working-tree",
    ) -> RepositoryContext:
        root = Path(root_path).resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {root}"
            )

        repository_id = (
            repository_id
            or root.name
        )

        files: list[SourceFile] = []

        for current_root, directories, filenames in os.walk(root):
            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in self.excluded_directories
            )

            for filename in sorted(filenames):
                absolute_path = (
                    Path(current_root) / filename
                )

                relative_path = (
                    absolute_path.relative_to(root)
                    .as_posix()
                )

                language = detect_language(
                    relative_path
                )

                if language is None:
                    continue

                try:
                    stat = absolute_path.stat()
                except OSError:
                    continue

                if stat.st_size > self.max_file_size_bytes:
                    continue

                try:
                    content = absolute_path.read_text(
                        encoding="utf-8"
                    )
                except (OSError, UnicodeDecodeError):
                    continue

                content_hash = hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest()

                files.append(
                    SourceFile(
                        path=relative_path,
                        content_hash=content_hash,
                        size_bytes=stat.st_size,
                        line_count=len(
                            content.splitlines()
                        ),
                        language=language,
                    )
                )

        files.sort(
            key=lambda source_file: source_file.path
        )

        return RepositoryContext(
            repository_id=repository_id,
            revision=revision,
            root_path=str(root),
            files=tuple(files),
        )
