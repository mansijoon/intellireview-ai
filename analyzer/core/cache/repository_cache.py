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

    CACHE_VERSION = "v2"
    LATEST_RESULTS_DIR = "latest"
    FILE_RESULTS_DIR = "files"

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
        self.latest_root = self.root / self.LATEST_RESULTS_DIR
        self.latest_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file_results_root = self.root / self.FILE_RESULTS_DIR
        self.file_results_root.mkdir(
            parents=True,
            exist_ok=True,
        )

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

    def _latest_path(
        self,
        analyzer_id: str,
    ) -> Path:
        safe_id = analyzer_id.replace("/", "_")
        return self.latest_root / f"{safe_id}.pickle"

    def file_key(
        self,
        analyzer_id: str,
        path: str,
        content_hash: str,
        *,
        variant: str = "",
    ) -> str:
        """Return a content-addressed key for one source-file analysis."""

        digest = hashlib.sha256()

        digest.update(self.CACHE_VERSION.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(analyzer_id.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(path.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(content_hash.encode("ascii"))
        digest.update(b"\\0")
        digest.update(variant.encode("utf-8"))

        return digest.hexdigest()

    def _file_path(self, key: str) -> Path:
        return self.file_results_root / f"{key}.pickle"

    def get_file_result(
        self,
        analyzer_id: str,
        path: str,
        content_hash: str,
        *,
        variant: str = "",
    ) -> Any | None:
        """Return a cached result for one file/content version."""

        path_obj = self._file_path(
            self.file_key(
                analyzer_id,
                path,
                content_hash,
                variant=variant,
            )
        )

        if not path_obj.exists():
            return None

        try:
            with path_obj.open("rb") as handle:
                return pickle.load(handle)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ImportError,
            ModuleNotFoundError,
        ):
            return None

    def set_file_result(
        self,
        analyzer_id: str,
        path: str,
        content_hash: str,
        value: Any,
        *,
        variant: str = "",
    ) -> None:
        """Persist a result for one file/content version."""

        target = self._file_path(
            self.file_key(
                analyzer_id,
                path,
                content_hash,
                variant=variant,
            )
        )

        temporary = target.with_suffix(".tmp")

        try:
            with temporary.open("wb") as handle:
                pickle.dump(
                    value,
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

            temporary.replace(target)

        finally:
            if temporary.exists():
                temporary.unlink(
                    missing_ok=True
                )

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

    def get_latest(
        self,
        analyzer_id: str,
    ) -> RepositoryAnalysisResult | None:
        """Return the most recently successful result for an analyzer."""

        path = self._latest_path(analyzer_id)

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

        if not isinstance(result, RepositoryAnalysisResult):
            return None

        if result.analyzer_id != analyzer_id:
            return None

        if result.status != RepositoryAnalysisStatus.SUCCESS:
            return None

        return result

    def set(
        self,
        repository: RepositoryContext,
        result: RepositoryAnalysisResult,
    ) -> None:
        if result.status != RepositoryAnalysisStatus.SUCCESS:
            return

        key = self.key(
            repository,
            result.analyzer_id,
        )

        target = self._path(key)
        latest = self._latest_path(result.analyzer_id)

        for destination in (target, latest):
            temporary = destination.with_suffix(".tmp")

            try:
                with temporary.open("wb") as handle:
                    pickle.dump(
                        result,
                        handle,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )

                temporary.replace(destination)

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
