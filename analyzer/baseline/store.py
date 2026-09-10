from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from analyzer.baseline.models import Baseline


class BaselineStore:
    """Persistent storage for the repository's selected baseline."""

    VERSION = "v1"

    def __init__(
        self,
        repository_root: str,
    ) -> None:
        self.root = (
            Path(repository_root).resolve()
            / ".intellireview-cache"
            / "baseline"
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path = self.root / "baseline.pickle"

    def save(
        self,
        baseline: Baseline,
    ) -> None:
        temporary = self.path.with_suffix(
            ".tmp"
        )

        try:
            with temporary.open("wb") as handle:
                pickle.dump(
                    baseline,
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )

            temporary.replace(self.path)

        finally:
            if temporary.exists():
                temporary.unlink(
                    missing_ok=True
                )

    def load(self) -> Baseline | None:
        if not self.path.exists():
            return None

        try:
            with self.path.open("rb") as handle:
                value: Any = pickle.load(handle)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ImportError,
            ModuleNotFoundError,
        ):
            return None

        if not isinstance(value, Baseline):
            return None

        return value

    def exists(self) -> bool:
        return self.path.exists()

    def clear(self) -> None:
        self.path.unlink(
            missing_ok=True
        )
