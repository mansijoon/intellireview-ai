from __future__ import annotations

import json
from typing import Any

from analyzer.security.sbom.models import (
    SBOMReport,
)


def _component_payload(
    component,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "library",
        "name": component.name,
        "version": component.version or "unknown",
        "scope": (
            "optional"
            if component.dependency_type == "optional"
            else "required"
        ),
    }

    if component.package_url:
        payload["purl"] = component.package_url

    if component.licenses:
        payload["licenses"] = [
            {
                "license": {
                    "id": license_id,
                }
            }
            for license_id in component.licenses
        ]

    return payload


def sbom_to_cyclonedx(
    report: SBOMReport,
) -> dict[str, Any]:
    """Convert the normalized SBOM into CycloneDX JSON."""

    return {
        "bomFormat": "CycloneDX",
        "specVersion": report.spec_version,
        "serialNumber": (
            "urn:uuid:intellireview-generated"
        ),
        "version": 1,
        "components": [
            _component_payload(component)
            for component in report.components
        ],
    }


def sbom_to_cyclonedx_json(
    report: SBOMReport,
) -> str:
    """Serialize an SBOM as deterministic CycloneDX JSON."""

    return json.dumps(
        sbom_to_cyclonedx(report),
        indent=2,
        sort_keys=True,
    )
