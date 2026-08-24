from __future__ import annotations

from pathlib import Path


LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
}


SUPPORTED_EXTENSIONS = frozenset(
    LANGUAGE_BY_EXTENSION
)


def detect_language(file_path: str) -> str | None:
    """Return the normalized language for a source file."""

    suffix = Path(file_path).suffix.lower()

    return LANGUAGE_BY_EXTENSION.get(suffix)
