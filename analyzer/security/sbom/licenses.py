from __future__ import annotations


PERMISSIVE_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "0BSD",
    "CC0-1.0",
    "Unlicense",
    "PSF-2.0",
    "PSFL",
    "Python Software Foundation License",
    "Zlib",
    "MPL-2.0",
}


WEAK_COPYLEFT_LICENSES = {
    "LGPL-2.0",
    "LGPL-2.0-only",
    "LGPL-2.0-or-later",
    "LGPL-2.1",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
}


STRONG_COPYLEFT_LICENSES = {
    "GPL-2.0",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
}


ALIASES = {
    "MIT License": "MIT",
    "BSD license": "BSD-2-Clause",
    "BSD License": "BSD-2-Clause",
    "BSD 2-Clause License": "BSD-2-Clause",
    "BSD 3-Clause License": "BSD-3-Clause",
    "ISC License": "ISC",
    "ISC License (ISCL)": "ISC",
    "Mozilla Public License 2.0": "MPL-2.0",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "PSF-2.0",
    "PSFL": "PSF-2.0",
}


def normalize_license(
    license_id: str,
) -> str:
    """Normalize common package-metadata license names."""

    normalized = (
        license_id
        .strip()
        .replace("  ", " ")
    )

    if not normalized:
        return ""

    return ALIASES.get(
        normalized,
        normalized,
    )


def classify_license(
    license_id: str,
) -> str:
    """Classify a normalized SPDX-compatible license."""

    normalized = normalize_license(
        license_id
    )

    if not normalized:
        return "unknown"

    if normalized in PERMISSIVE_LICENSES:
        return "permissive"

    if normalized in WEAK_COPYLEFT_LICENSES:
        return "weak-copyleft"

    if normalized in STRONG_COPYLEFT_LICENSES:
        return "strong-copyleft"

    return "unknown"
