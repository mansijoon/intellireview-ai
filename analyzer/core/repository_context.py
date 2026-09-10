from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from analyzer.core.context import AnalysisContext
from analyzer.core.models import SourceFile


@dataclass(slots=True)
class RepositoryContext:
    """Shared context for repository-wide analysis."""

    repository_id: str
    revision: str
    root_path: str

    files: tuple[SourceFile, ...] = field(default_factory=tuple)
    source_contents: dict[str, str] = field(default_factory=dict)

    configuration: dict[str, Any] = field(default_factory=dict)

    @property
    def analysis_scope(self) -> frozenset[str] | None:
        """
        Return the repository files that require file-local analysis.

        None means the full repository is in scope. An explicit set
        allows incremental analyzers to process only changed/affected
        files while preserving the complete RepositoryContext.
        """
        value = self.configuration.get(
            "_intellireview_analysis_scope"
        )

        if value is None:
            return None

        return frozenset(value)

    def files_in_analysis_scope(self):
        """Yield repository files selected for incremental analysis."""
        scope = self.analysis_scope

        if scope is None:
            yield from self.files
            return

        for source_file in self.files:
            if source_file.path in scope:
                yield source_file

    _contexts: dict[str, AnalysisContext] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self.repository_id.strip():
            raise ValueError("repository_id must not be empty")

        if not self.revision.strip():
            raise ValueError("revision must not be empty")

        if not self.root_path.strip():
            raise ValueError("root_path must not be empty")

    @property
    def file_count(self) -> int:
        return len(self.files)

    def get_file(
        self,
        relative_path: str,
    ) -> SourceFile | None:
        for source_file in self.files:
            if source_file.path == relative_path:
                return source_file

        return None

    def get_context(
        self,
        relative_path: str,
    ) -> AnalysisContext:
        existing = self._contexts.get(relative_path)

        if existing is not None:
            return existing

        source_file = self.get_file(relative_path)

        if source_file is None:
            raise KeyError(
                f"Unknown repository file: {relative_path}"
            )

        source = self.source_contents.get(relative_path)

        if source is None:
            absolute_path = (
                Path(self.root_path) / relative_path
            )

            try:
                source = absolute_path.read_text(
                    encoding="utf-8"
                )
            except (OSError, UnicodeDecodeError) as exc:
                raise RuntimeError(
                    f"Unable to read repository file: "
                    f"{relative_path}"
                ) from exc

        context = AnalysisContext(
            file_path=relative_path,
            source=source,
            language=source_file.language,
        )

        self._contexts[relative_path] = context

        return context

    def iter_contexts(self):
        """Yield analysis contexts in deterministic path order."""

        for source_file in self.files:
            yield self.get_context(
                source_file.path
            )

    def set_artifact(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.configuration[f"artifact:{key}"] = value

    def get_artifact(
        self,
        key: str,
    ) -> Any | None:
        return self.configuration.get(
            f"artifact:{key}"
        )

    def source_paths(self) -> tuple[str, ...]:
        return tuple(
            source_file.path
            for source_file in self.files
        )
