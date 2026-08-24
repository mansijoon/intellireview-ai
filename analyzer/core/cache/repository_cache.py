from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any

from analyzer.core.cache.invalidation import RepositoryChangeSet

from analyzer.core.models import (
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext


class RepositoryAnalysisCache:
    """Persistent content-addressed cache for analyzer results."""

    CACHE_VERSION = "v1"

    def __init__(
        self,
        root_path: str,
    ) -> None:
        self.root = (
            Path(root_path).resolve()
            / ".intellireview-cache"
            / "analysis"
        )
        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.snapshot_path = self.root / "repository-snapshot.pickle"

    def repository_fingerprint(
        self,
        repository: RepositoryContext,
    ) -> str:
        digest = hashlib.sha256()

        digest.update(
            self.CACHE_VERSION.encode("utf-8")
        )

        for source_file in repository.files:
            digest.update(
                source_file.path.encode("utf-8")
            )
            digest.update(
                b"\0"
            )
            digest.update(
                source_file.content_hash.encode(
                    "ascii"
                )
            )
            digest.update(
                b"\0"
            )
            digest.update(
                source_file.language.encode("utf-8")
            )
            digest.update(
                b"\0"
            )

        return digest.hexdigest()

    def snapshot(
        self,
        repository: RepositoryContext,
    ) -> dict[str, str]:
        return {
            source_file.path: source_file.content_hash
            for source_file in repository.files
        }

    def load_snapshot(self) -> dict[str, str] | None:
        if not self.snapshot_path.exists():
            return None

        try:
            with self.snapshot_path.open("rb") as handle:
                snapshot = pickle.load(handle)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ImportError,
            ModuleNotFoundError,
        ):
            return None

        if not isinstance(snapshot, dict):
            return None

        if not all(
            isinstance(path, str)
            and isinstance(content_hash, str)
            for path, content_hash in snapshot.items()
        ):
            return None

        return snapshot

    def save_snapshot(
        self,
        repository: RepositoryContext,
    ) -> None:
        snapshot = self.snapshot(repository)
        temporary = self.snapshot_path.with_suffix(".tmp")

        try:
            with temporary.open("wb") as handle:
                pickle.dump(
                    snapshot,
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

            temporary.replace(self.snapshot_path)

        finally:
            if temporary.exists():
                temporary.unlink(
                    missing_ok=True
                )

    def change_set(
        self,
        previous: dict[str, str],
        repository: RepositoryContext,
    ) -> RepositoryChangeSet:
        current = self.snapshot(repository)

        previous_paths = set(previous)
        current_paths = set(current)

        added = frozenset(
            current_paths - previous_paths
        )

        deleted = frozenset(
            previous_paths - current_paths
        )

        modified = frozenset(
            path
            for path in previous_paths & current_paths
            if previous[path] != current[path]
        )

        return RepositoryChangeSet(
            added=added,
            modified=modified,
            deleted=deleted,
        )

    def key(
        self,
        repository: RepositoryContext,
        analyzer_id: str,
    ) -> str:
        digest = hashlib.sha256()

        digest.update(
            self.repository_fingerprint(
                repository
            ).encode("ascii")
        )

        digest.update(b"\0")

        digest.update(
            analyzer_id.encode("utf-8")
        )

        return digest.hexdigest()

    def _path(
        self,
        key: str,
    ) -> Path:
        return self.root / f"{key}.pickle"

    def get(
        self,
        repository: RepositoryContext,
        analyzer_id: str,
    ) -> RepositoryAnalysisResult | None:
        path = self._path(
            self.key(
                repository,
                analyzer_id,
            )
        )

        if not path.exists():
            return None

        try:
            with path.open("rb") as handle:
                result: Any = pickle.load(handle)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ImportError,
            ModuleNotFoundError,
        ):
            return None

        if not isinstance(
            result,
            RepositoryAnalysisResult,
        ):
            return None

        if result.analyzer_id != analyzer_id:
            return None

        if (
            result.status
            != RepositoryAnalysisStatus.SUCCESS
        ):
            return None

        return result

    def set(
        self,
        repository: RepositoryContext,
        result: RepositoryAnalysisResult,
    ) -> None:
        if (
            result.status
            != RepositoryAnalysisStatus.SUCCESS
        ):
            return

        key = self.key(
            repository,
            result.analyzer_id,
        )

        target = self._path(key)
        temporary = target.with_suffix(
            ".tmp"
        )

        try:
            with temporary.open("wb") as handle:
                pickle.dump(
                    result,
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

            temporary.replace(target)

        finally:
            if temporary.exists():
                temporary.unlink(
                    missing_ok=True
                )

    def clear(self) -> None:
        if not self.root.exists():
            return

        for path in self.root.glob(
            "*.pickle"
        ):
            path.unlink(
                missing_ok=True
            )
