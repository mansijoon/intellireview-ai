from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from analyzer.core.models import SourceLocation


class CallResolutionStatus(StrEnum):
    """Resolution state of a statically observed call."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class CallRelationship:
    """A statically observed call from one symbol to another."""

    caller_symbol_id: str
    callee_name: str
    location: SourceLocation

    callee_symbol_id: str | None = None

    resolution_status: CallResolutionStatus = (
        CallResolutionStatus.UNRESOLVED
    )


@dataclass(slots=True)
class CallGraph:
    """Repository-wide call relationship graph."""

    calls: list[CallRelationship] = field(
        default_factory=list
    )

    def add_call(
        self,
        call: CallRelationship,
    ) -> None:
        self.calls.append(call)

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def resolved_call_count(self) -> int:
        return sum(
            call.resolution_status
            == CallResolutionStatus.RESOLVED
            for call in self.calls
        )

    @property
    def unresolved_call_count(self) -> int:
        return sum(
            call.resolution_status
            == CallResolutionStatus.UNRESOLVED
            for call in self.calls
        )

    def calls_from(
        self,
        caller_symbol_id: str,
    ) -> tuple[CallRelationship, ...]:
        return tuple(
            call
            for call in self.calls
            if call.caller_symbol_id
            == caller_symbol_id
        )

    def calls_to(
        self,
        callee_symbol_id: str,
    ) -> tuple[CallRelationship, ...]:
        return tuple(
            call
            for call in self.calls
            if call.callee_symbol_id
            == callee_symbol_id
        )
