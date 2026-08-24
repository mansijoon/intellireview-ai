from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from analyzer.core.models import SourceLocation


class SymbolResolutionStatus(StrEnum):
    """Resolution state of a statically observed symbol reference."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class SymbolNode:
    """A symbol defined in the repository."""

    symbol_id: str
    name: str
    kind: str
    module: str
    location: SourceLocation
    parent_id: str | None = None

    children: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class SymbolReference:
    """A statically observed reference to a symbol."""

    source_symbol_id: str
    referenced_name: str
    location: SourceLocation

    target_symbol_id: str | None = None

    resolution_status: SymbolResolutionStatus = (
        SymbolResolutionStatus.UNRESOLVED
    )


@dataclass(slots=True)
class SymbolGraph:
    """Repository-wide symbol graph."""

    symbols: dict[str, SymbolNode] = field(
        default_factory=dict
    )

    references: list[SymbolReference] = field(
        default_factory=list
    )

    def add_symbol(
        self,
        symbol: SymbolNode,
    ) -> None:
        if symbol.symbol_id in self.symbols:
            raise ValueError(
                f"Symbol already exists: {symbol.symbol_id}"
            )

        self.symbols[symbol.symbol_id] = symbol

    def add_reference(
        self,
        reference: SymbolReference,
    ) -> None:
        self.references.append(reference)

    def get_symbol(
        self,
        symbol_id: str,
    ) -> SymbolNode | None:
        return self.symbols.get(symbol_id)

    def __len__(self) -> int:
        return len(self.symbols)

    @property
    def symbol_count(self) -> int:
        return len(self.symbols)

    @property
    def reference_count(self) -> int:
        return len(self.references)

    def symbols_by_kind(
        self,
        kind: str,
    ) -> tuple[SymbolNode, ...]:
        return tuple(
            symbol
            for symbol in self.symbols.values()
            if symbol.kind == kind
        )
