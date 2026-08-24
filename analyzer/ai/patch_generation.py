from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedPatch:
    file_path: str
    original: str
    replacement: str
    reason: str


def generate_patch(
    *,
    file_path: str,
    source: str,
    original: str,
    replacement: str,
    reason: str,
) -> GeneratedPatch:
    if not file_path.strip():
        raise ValueError("file_path must not be empty")

    if not original:
        raise ValueError("original must not be empty")

    if original not in source:
        raise ValueError(
            "original code was not found in source"
        )

    if not replacement:
        raise ValueError("replacement must not be empty")

    if original == replacement:
        raise ValueError(
            "replacement must differ from original"
        )

    if not reason.strip():
        raise ValueError("reason must not be empty")

    return GeneratedPatch(
        file_path=file_path,
        original=original,
        replacement=replacement,
        reason=reason,
    )


def apply_patch(
    source: str,
    patch: GeneratedPatch,
) -> str:
    if patch.original not in source:
        raise ValueError(
            "patch target no longer exists in source"
        )

    return source.replace(
        patch.original,
        patch.replacement,
        1,
    )
