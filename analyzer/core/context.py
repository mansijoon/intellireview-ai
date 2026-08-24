from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AnalysisContext:
    """Shared context for analyzing one source file."""

    file_path: str
    source: str
    language: str = "python"
    configuration: dict[str, Any] = field(default_factory=dict)

    _ast: ast.AST | None = field(default=None, init=False, repr=False)
    _ast_error: SyntaxError | None = field(
        default=None,
        init=False,
        repr=False,
    )

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(
            self.source.encode("utf-8")
        ).hexdigest()

    @property
    def line_count(self) -> int:
        if not self.source:
            return 0

        return len(self.source.splitlines())

    @property
    def ast_tree(self) -> ast.AST | None:
        """Parse Python source once and cache the AST."""

        if self.language.lower() not in {
            "python",
            "py",
        }:
            return None

        if self._ast is not None:
            return self._ast

        if self._ast_error is not None:
            return None

        try:
            self._ast = ast.parse(
                self.source,
                filename=self.file_path,
            )
        except SyntaxError as exc:
            self._ast_error = exc
            return None

        return self._ast

    @property
    def syntax_error(self) -> SyntaxError | None:
        """Return the cached syntax error, if parsing failed."""

        _ = self.ast_tree
        return self._ast_error

    def get_artifact(
        self,
        key: str,
    ) -> Any | None:
        return self.configuration.get(
            f"artifact:{key}"
        )

    def set_artifact(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.configuration[f"artifact:{key}"] = value
