from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.core.models import SourceLocation


@dataclass(frozen=True, slots=True)
class TaintSource:
    source_id: str
    name: str
    location: SourceLocation
    kind: str


@dataclass(frozen=True, slots=True)
class TaintSink:
    sink_id: str
    name: str
    location: SourceLocation
    kind: str


@dataclass(frozen=True, slots=True)
class TaintPath:
    source: TaintSource
    sink: TaintSink
    propagation: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(slots=True)
class TaintReport:
    file_count: int
    source_count: int
    sink_count: int
    finding_count: int
    affected_file_count: int
    paths: list[TaintPath] = field(
        default_factory=list
    )
