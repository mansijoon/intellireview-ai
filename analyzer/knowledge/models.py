from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class KnowledgeFile:
    file_path: str
    language: str
    size_bytes: int
    line_count: int


@dataclass(frozen=True, slots=True)
class KnowledgeSymbol:
    symbol_id: str
    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int | None = None
    parent_symbol_id: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeCall:
    caller_symbol_id: str | None
    callee_symbol_id: str | None
    callee_name: str
    file_path: str
    line_start: int
    resolved: bool


@dataclass(frozen=True, slots=True)
class KnowledgeDependency:
    source: str
    target: str
    dependency_type: str


@dataclass(frozen=True, slots=True)
class KnowledgeFinding:
    rule_id: str
    analyzer: str
    severity: str
    message: str
    file_path: str | None
    line_start: int | None
    category: str | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class RepositoryKnowledgeModel:
    repository_id: str
    revision: str
    files: tuple[KnowledgeFile, ...] = ()
    symbols: tuple[KnowledgeSymbol, ...] = ()
    calls: tuple[KnowledgeCall, ...] = ()
    dependencies: tuple[KnowledgeDependency, ...] = ()
    findings: tuple[KnowledgeFinding, ...] = ()

    symbol_by_id: dict[str, KnowledgeSymbol] = field(
        default_factory=dict
    )
    symbols_by_file: dict[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    calls_by_caller: dict[str, tuple[KnowledgeCall, ...]] = field(
        default_factory=dict
    )
    calls_by_callee: dict[str, tuple[KnowledgeCall, ...]] = field(
        default_factory=dict
    )
    dependencies_by_source: dict[
        str, tuple[KnowledgeDependency, ...]
    ] = field(default_factory=dict)
    dependencies_by_target: dict[
        str, tuple[KnowledgeDependency, ...]
    ] = field(default_factory=dict)
    findings_by_file: dict[
        str, tuple[KnowledgeFinding, ...]
    ] = field(default_factory=dict)

    metadata: dict[str, Any] = field(
        default_factory=dict
    )
