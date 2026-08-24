from __future__ import annotations

from importlib import metadata

from analyzer.security.sbom.models import SBOMComponent


def _normalize_version(
    version: str | None,
) -> str | None:
    if not version:
        return None

    version = version.strip()

    if version.startswith("=="):
        return version[2:]

    return version


def _package_url(
    name: str,
    version: str | None,
) -> str | None:
    if not version:
        return None

    return (
        f"pkg:pypi/{name.lower()}"
        f"@{version}"
    )


def resolve_package_metadata(
    dependency,
) -> SBOMComponent:
    """
    Resolve Python package metadata for one dependency.

    Installed distribution metadata is used when available.
    Missing metadata is represented explicitly rather than
    guessed.
    """

    version = _normalize_version(
        dependency.version
    )

    licenses: list[str] = []

    try:
        package_metadata = metadata.metadata(
            dependency.name
        )

        raw_license = (
            package_metadata.get("License")
            or ""
        ).strip()

        if raw_license:
            licenses.append(
                raw_license
            )

        classifiers = (
            package_metadata.get_all(
                "Classifier"
            )
            or []
        )

        for classifier in classifiers:
            prefix = (
                "License :: OSI Approved :: "
            )

            if classifier.startswith(prefix):
                license_name = (
                    classifier[len(prefix):]
                    .strip()
                )

                if license_name:
                    licenses.append(
                        license_name
                    )

    except metadata.PackageNotFoundError:
        pass

    return SBOMComponent(
        name=dependency.name,
        version=version,
        ecosystem="PyPI",
        package_url=_package_url(
            dependency.name,
            version,
        ),
        source_file=dependency.source_file,
        dependency_type=dependency.dependency_type,
        licenses=tuple(
            dict.fromkeys(licenses)
        ),
    )
