from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ArchitectureViolationType(StrEnum):
    DEPENDENCY_CYCLE = "dependency_cycle"
    FORBIDDEN_DEPENDENCY = "forbidden_dependency"
    LAYER_VIOLATION = "layer_violation"
    HIGH_COUPLING = "high_coupling"


@dataclass(frozen=True, slots=True)
class ArchitectureViolation:
    """A deterministic architectural validation violation."""

    violation_type: ArchitectureViolationType
    severity: str
    message: str
    source_module: str | None = None
    target_module: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError(
                "message must not be empty"
            )

        if not self.severity.strip():
            raise ValueError(
                "severity must not be empty"
            )
