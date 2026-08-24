from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from analyzer.core.context import AnalysisContext
from analyzer.core.engine.repository_analyzer import (
    RepositoryAnalyzer,
)
from analyzer.core.models import (
    AnalysisResult,
    Finding,
    RepositorySnapshot,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.rules import AnalysisRule, RuleRegistry


@dataclass(slots=True)
class AnalysisEngine:
    """Orchestrates file-level and repository-level analysis."""

    rules: list[AnalysisRule]

    repository_analyzers: list[RepositoryAnalyzer] = field(
        default_factory=list
    )

    @classmethod
    def from_registry(
        cls,
        registry: RuleRegistry,
        repository_analyzers: list[RepositoryAnalyzer] | None = None,
    ) -> "AnalysisEngine":
        return cls(
            rules=registry.create_rules(),
            repository_analyzers=(
                repository_analyzers
                if repository_analyzers is not None
                else []
            ),
        )

    def analyze_context(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for rule in self.rules:
            findings.extend(
                rule.analyze(
                    context=context
                )
            )

        return findings

    def analyze_file(
        self,
        source: str,
        file_path: str,
        language: str = "python",
    ) -> list[Finding]:
        context = AnalysisContext(
            source=source,
            file_path=file_path,
            language=language,
        )

        return self.analyze_context(
            context
        )

    def analyze_repository(
        self,
        repository: RepositoryContext,
    ) -> list[Finding]:
        """
        Run repository-level analyzers followed by file-level rules.

        Repository analyzers populate shared repository artifacts that
        subsequent analysis phases can consume.
        """

        for analyzer in self.repository_analyzers:
            analyzer.analyze(
                repository
            )

        findings: list[Finding] = []

        for context in repository.iter_contexts():
            findings.extend(
                self.analyze_context(
                    context
                )
            )

        return findings

    def analyze_repository_result(
        self,
        repository: RepositoryContext,
    ) -> AnalysisResult:
        """Return the canonical analysis result."""

        started_at = datetime.now(
            timezone.utc
        )

        findings = self.analyze_repository(
            repository
        )

        completed_at = datetime.now(
            timezone.utc
        )

        snapshot = RepositorySnapshot(
            repository_id=repository.repository_id,
            revision=repository.revision,
            root_path=repository.root_path,
            files=repository.files,
        )

        return AnalysisResult(
            repository=snapshot,
            findings=tuple(findings),
            started_at=started_at,
            completed_at=completed_at,
        )
