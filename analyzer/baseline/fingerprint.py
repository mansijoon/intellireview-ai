from __future__ import annotations

import hashlib
import re

from analyzer.core.models import Finding


_WHITESPACE = re.compile(r"\s+")


def _normalize(value: str) -> str:
    return _WHITESPACE.sub(
        " ",
        value.strip().lower(),
    )


def finding_fingerprint(
    finding: Finding,
) -> str:
    """
    Generate a stable finding identity.

    Location line numbers are intentionally excluded so that a finding
    can survive source-line movement.

    The identity is based only on semantic finding metadata. The current
    repository working tree is never consulted, which keeps fingerprints
    independent of the checkout state and Git revision.
    """

    components = (
        _normalize(finding.analyzer),
        _normalize(finding.rule_id),
        _normalize(finding.title),
        _normalize(finding.location.file_path),
    )

    payload = "\0".join(
        components
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()
