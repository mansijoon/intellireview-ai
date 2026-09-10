from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedPatch:
    file_path: str
    original: str
    replacement: str
    reason: str
    line_start: int | None = None
    line_end: int | None = None


def generate_patch(
    *,
    file_path: str,
    source: str,
    original: str,
    replacement: str,
    reason: str,
    line_start: int | None = None,
    line_end: int | None = None,
) -> GeneratedPatch:
    if not file_path.strip():
        raise ValueError("file_path must not be empty")

    if not original:
        raise ValueError("original must not be empty")

    if original not in source:
        raise ValueError(
            "original code was not found in source"
        )

    if original == replacement:
        raise ValueError(
            "replacement must differ from original"
        )

    if not reason.strip():
        raise ValueError("reason must not be empty")

    if line_start is not None:
        if line_start < 1:
            raise ValueError(
                "line_start must be >= 1"
            )

        if line_end is None:
            line_end = line_start

        if line_end < line_start:
            raise ValueError(
                "line_end must be >= line_start"
            )

        source_lines = source.splitlines(
            keepends=True
        )

        if line_start > len(source_lines):
            raise ValueError(
                "line_start exceeds source line count"
            )

        if line_end > len(source_lines):
            raise ValueError(
                "line_end exceeds source line count"
            )

        targeted_source = "".join(
            source_lines[
                line_start - 1:line_end
            ]
        )

        if original not in targeted_source:
            raise ValueError(
                "original code does not occur within "
                "the requested source location"
            )

        if targeted_source.count(original) > 1:
            raise ValueError(
                "original code occurs multiple times "
                "within the requested source location"
            )

    return GeneratedPatch(
        file_path=file_path,
        original=original,
        replacement=replacement,
        reason=reason,
        line_start=line_start,
        line_end=line_end,
    )


def apply_patch(
    source: str,
    patch: GeneratedPatch,
) -> str:
    if patch.original not in source:
        raise ValueError(
            "patch target no longer exists in source"
        )

    if patch.line_start is None:
        return source.replace(
            patch.original,
            patch.replacement,
            1,
        )

    source_lines = source.splitlines(
        keepends=True
    )

    line_start = patch.line_start
    line_end = patch.line_end or line_start

    if line_start < 1:
        raise ValueError(
            "patch line_start must be >= 1"
        )

    if line_end < line_start:
        raise ValueError(
            "patch line_end must be >= line_start"
        )

    if line_end > len(source_lines):
        raise ValueError(
            "patch line_end exceeds source line count"
        )

    targeted_source = "".join(
        source_lines[
            line_start - 1:line_end
        ]
    )

    if targeted_source.count(patch.original) != 1:
        raise ValueError(
            "patch target is not uniquely located "
            "within the requested source location"
        )

    patched_target = targeted_source.replace(
        patch.original,
        patch.replacement,
        1,
    )

    return (
        "".join(
            source_lines[:line_start - 1]
        )
        + patched_target
        + "".join(
            source_lines[line_end:]
        )
    )
