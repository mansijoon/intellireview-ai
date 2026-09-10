from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from analyzer.dependency.models import DependencyGraph


@dataclass(frozen=True, slots=True)
class RepositoryChangeSet:
    added: frozenset[str]
    modified: frozenset[str]
    deleted: frozenset[str]

    @property
    def changed(self) -> frozenset[str]:
        return (
            self.added
            | self.modified
            | self.deleted
        )

    @property
    def is_empty(self) -> bool:
        return not self.changed


class DependencyInvalidator:
    """Computes repository modules affected by changed files."""

    def affected_modules(
        self,
        graph: DependencyGraph,
        changed_files: Iterable[str],
    ) -> frozenset[str]:
        module_by_path = {
            module.path: module.name
            for module in graph.modules.values()
        }

        affected = {
            module_by_path[path]
            for path in changed_files
            if path in module_by_path
        }

        queue = list(affected)

        while queue:
            current = queue.pop()

            module = graph.get_module(current)

            if module is None:
                continue

            for dependent in module.imported_by:
                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)

        return frozenset(affected)


class AnalyzerInvalidator:
    """
    Determines which repository analyzers must be recomputed.

    This is intentionally conservative: graph-dependent analyzers
    are invalidated together when source/dependency structure changes.
    """

    GRAPH_ANALYZERS = frozenset(
        {
            "dependency",
            "architecture",
            "symbol",
            "call",
            "architecture_validation",
            "change_impact",
            "repository_risk",
            "taint",
            "knowledge",
        }
    )

    STATIC_ANALYZERS = frozenset(
        {
            "static",
            "complexity",
            "maintainability",
            "duplication",
            "dead_code",
            "performance",
            "reliability",
            "security",
            "sbom",
        }
    )

    def __init__(self, registry=None):
        self.registry = registry

    def invalidated_analyzers(
        self,
        change_set: RepositoryChangeSet,
        *,
        changed_modules: Iterable[str] = (),
    ) -> frozenset[str]:
        if change_set.is_empty:
            return frozenset()

        if self.registry is None:
            return frozenset()

        metadata = {
            analyzer.metadata.analyzer_id: analyzer.metadata
            for analyzer in self.registry.create_analyzers()
        }

        invalidated = {
            analyzer_id
            for analyzer_id, item in metadata.items()
            if item.source_sensitive
        }

        changed = True
        while changed:
            changed = False

            for analyzer_id, item in metadata.items():
                if analyzer_id in invalidated:
                    continue

                if item.depends_on & invalidated:
                    invalidated.add(analyzer_id)
                    changed = True

        return frozenset(invalidated)
