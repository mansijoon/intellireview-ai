from __future__ import annotations

from typing import Any

import requests

from analyzer.security.dependency.models import (
    PackageDependency,
    VulnerabilityAdvisory,
)
from analyzer.security.models import (
    SecuritySeverity,
)


OSV_QUERY_BATCH_URL = (
    "https://api.osv.dev/v1/querybatch"
)

_OSV_TIMEOUT_SECONDS = 15


def _severity_from_osv(
    vulnerability: dict[str, Any],
) -> SecuritySeverity:
    """Resolve OSV severity using database severity first.

    OSV/GitHub frequently provides an explicit normalized severity
    alongside CVSS vectors. That value is preferred because it avoids
    depending on the installed CVSS library's vector-version support.
    CVSS parsing is retained as a fallback.
    """

    database_specific = vulnerability.get(
        "database_specific",
        {},
    )

    database_severity = str(
        database_specific.get(
            "severity",
            "",
        )
    ).strip().lower()

    severity_map = {
        "critical": SecuritySeverity.CRITICAL,
        "high": SecuritySeverity.HIGH,
        "moderate": SecuritySeverity.MEDIUM,
        "medium": SecuritySeverity.MEDIUM,
        "low": SecuritySeverity.LOW,
    }

    if database_severity in severity_map:
        return severity_map[database_severity]

    severity_entries = vulnerability.get(
        "severity",
        [],
    )

    try:
        from cvss import CVSS2, CVSS3
    except ImportError:
        CVSS2 = None
        CVSS3 = None

    for entry in severity_entries:
        score = str(
            entry.get(
                "score",
                "",
            )
        ).strip()

        if not score:
            continue

        try:
            cvss_score = None

            if (
                CVSS3 is not None
                and score.startswith("CVSS:3.")
            ):
                cvss_score = CVSS3(
                    score
                ).scores()[0]

            elif (
                CVSS2 is not None
                and score.startswith("AV:")
            ):
                cvss_score = CVSS2(
                    score
                ).scores()[0]

            elif not score.startswith("CVSS:"):
                cvss_score = float(score)

            if cvss_score is None:
                continue

            if cvss_score >= 9.0:
                return SecuritySeverity.CRITICAL

            if cvss_score >= 7.0:
                return SecuritySeverity.HIGH

            if cvss_score >= 4.0:
                return SecuritySeverity.MEDIUM

            return SecuritySeverity.LOW

        except Exception:
            continue

    return SecuritySeverity.MEDIUM


def _fetch_vulnerability(
    advisory_id: str,
) -> dict[str, Any]:
    """Fetch the complete OSV vulnerability record."""

    response = requests.get(
        f"https://api.osv.dev/v1/vulns/{advisory_id}",
        timeout=_OSV_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "OSV vulnerability response must be an object"
        )

    return payload


def _extract_version_ranges(
    vulnerability: dict[str, Any],
) -> tuple[str, ...]:
    ranges = []

    for affected in vulnerability.get(
        "affected",
        [],
    ):
        for version_range in affected.get(
            "ranges",
            [],
        ):
            events = version_range.get(
                "events",
                [],
            )

            for event in events:
                if "introduced" in event:
                    ranges.append(
                        f"introduced:{event['introduced']}"
                    )

                if "fixed" in event:
                    ranges.append(
                        f"fixed:{event['fixed']}"
                    )

                if "last_affected" in event:
                    ranges.append(
                        "last_affected:"
                        f"{event['last_affected']}"
                    )

    return tuple(ranges)


def _convert_vulnerability(
    vulnerability: dict[str, Any],
    dependency: PackageDependency,
) -> VulnerabilityAdvisory:
    aliases = tuple(
        str(alias)
        for alias in vulnerability.get(
            "aliases",
            [],
        )
    )

    references = tuple(
        str(reference.get("url"))
        for reference in vulnerability.get(
            "references",
            []
        )
        if reference.get("url")
    )

    return VulnerabilityAdvisory(
        advisory_id=str(
            vulnerability.get(
                "id",
                "UNKNOWN",
            )
        ),
        package_name=dependency.name,
        severity=_severity_from_osv(
            vulnerability
        ),
        summary=str(
            vulnerability.get(
                "summary",
                "Known vulnerability.",
            )
        ),
        affected_versions=(
            _extract_version_ranges(
                vulnerability
            )
        ),
        aliases=aliases,
        references=references,
    )


def query_osv_batch(
    dependencies: list[PackageDependency],
) -> dict[
    tuple[str, str],
    tuple[VulnerabilityAdvisory, ...],
]:
    """
    Query OSV for concrete dependency versions.

    The batch endpoint is used to discover affected advisory IDs.
    The batch endpoint intentionally returns only lightweight advisory
    metadata, so each advisory is subsequently hydrated through the
    OSV vulnerability-detail endpoint before normalization.

    Dependencies without an exact version are skipped because
    claiming vulnerability status without a resolved version
    would create false positives.
    """

    queries = []
    query_dependencies = []

    for dependency in dependencies:
        if not dependency.version:
            continue

        if not dependency.version.startswith(
            "=="
        ):
            continue

        version = dependency.version[2:]

        queries.append(
            {
                "package": {
                    "name": dependency.name,
                    "ecosystem": "PyPI",
                },
                "version": version,
            }
        )

        query_dependencies.append(
            dependency
        )

    if not queries:
        return {}

    response = requests.post(
        OSV_QUERY_BATCH_URL,
        json={
            "queries": queries,
        },
        timeout=_OSV_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    payload = response.json()

    results = payload.get(
        "results",
        [],
    )

    vulnerabilities = {}

    detail_cache: dict[
        str,
        dict[str, Any],
    ] = {}

    for dependency, result in zip(
        query_dependencies,
        results,
    ):
        converted = []

        for vulnerability_ref in result.get(
            "vulns",
            [],
        ):
            advisory_id = str(
                vulnerability_ref.get(
                    "id",
                    "",
                )
            ).strip()

            if not advisory_id:
                continue

            if advisory_id not in detail_cache:
                detail_cache[
                    advisory_id
                ] = _fetch_vulnerability(
                    advisory_id
                )

            vulnerability = detail_cache[
                advisory_id
            ]

            converted.append(
                _convert_vulnerability(
                    vulnerability,
                    dependency,
                )
            )

        vulnerabilities[
            (
                dependency.name,
                dependency.version,
            )
        ] = tuple(converted)

    return vulnerabilities

