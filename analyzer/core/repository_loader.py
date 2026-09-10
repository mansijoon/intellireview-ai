from __future__ import annotations

import hashlib
import os
from pathlib import Path

from analyzer.core.git_repository import GitRepository
from analyzer.core.language import detect_language
from analyzer.core.models import SourceFile
from analyzer.core.repository_context import RepositoryContext


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
    """Build a RepositoryContext from a working tree or Git revision."""

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

        repository_id = repository_id or root.name

        if revision == "working-tree":
            return self._load_working_tree(
                root,
                repository_id,
                revision,
            )

        return self._load_git_revision(
            root,
            repository_id,
            revision,
        )

    def _load_working_tree(
        self,
        root: Path,
        repository_id: str,
        revision: str,
    ) -> RepositoryContext:
        files: list[SourceFile] = []
        contents: dict[str, str] = {}

        for current_root, directories, filenames in os.walk(root):
            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in self.excluded_directories
            )

            for filename in sorted(filenames):
                absolute_path = Path(current_root) / filename

                relative_path = (
                    absolute_path.relative_to(root).as_posix()
                )

                source_file = self._build_source_file(
                    relative_path,
                    absolute_path.read_bytes()
                    if self._readable_file(absolute_path)
                    else None,
                )

                if source_file is None:
                    continue

                files.append(source_file)

                try:
                    contents[relative_path] = (
                        absolute_path.read_text(
                            encoding="utf-8"
                        )
                    )
                except (OSError, UnicodeDecodeError):
                    continue

        files.sort(key=lambda source_file: source_file.path)

        return RepositoryContext(
            repository_id=repository_id,
            revision=revision,
            root_path=str(root),
            files=tuple(files),
            source_contents=contents,
        )

    def _load_git_revision(
        self,
        root: Path,
        repository_id: str,
        revision: str,
    ) -> RepositoryContext:
        repository = GitRepository(str(root))
        resolved_revision = repository.resolve_revision(revision)

        files: list[SourceFile] = []
        contents: dict[str, str] = {}

        for relative_path in repository.list_files(
            resolved_revision
        ):
            if self._is_excluded(relative_path):
                continue

            language = detect_language(relative_path)

            if language is None:
                continue

            try:
                raw = repository.read_file(
                    resolved_revision,
                    relative_path,
                )
            except (FileNotFoundError, IsADirectoryError):
                continue

            if len(raw) > self.max_file_size_bytes:
                continue

            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue

            content_hash = hashlib.sha256(raw).hexdigest()

            files.append(
                SourceFile(
                    path=relative_path,
                    content_hash=content_hash,
                    size_bytes=len(raw),
                    line_count=len(content.splitlines()),
                    language=language,
                )
            )

            contents[relative_path] = content

        files.sort(key=lambda source_file: source_file.path)

        return RepositoryContext(
            repository_id=repository_id,
            revision=resolved_revision,
            root_path=str(root),
            files=tuple(files),
            source_contents=contents,
        )

    def _build_source_file(
        self,
        relative_path: str,
        raw: bytes | None,
    ) -> SourceFile | None:
        if raw is None:
            return None

        language = detect_language(relative_path)

        if language is None:
            return None

        if len(raw) > self.max_file_size_bytes:
            return None

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            return None

        return SourceFile(
            path=relative_path,
            content_hash=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),
            line_count=len(content.splitlines()),
            language=language,
        )

    def _readable_file(self, path: Path) -> bool:
        try:
            return (
                path.is_file()
                and path.stat().st_size
                <= self.max_file_size_bytes
            )
        except OSError:
            return False

    def _is_excluded(self, relative_path: str) -> bool:
        parts = Path(relative_path).parts

        return any(
            part in self.excluded_directories
            for part in parts
        )
