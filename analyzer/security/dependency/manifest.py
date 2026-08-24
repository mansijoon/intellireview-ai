from __future__ import annotations

import re
import tomllib
from pathlib import Path

from analyzer.security.dependency.models import (
    PackageDependency,
)


_REQUIREMENT_RE = re.compile(
    r"^\s*"
    r"([A-Za-z0-9_.-]+)"
    r"\s*"
    r"(?:"
    r"([<>=!~]+)"
    r"\s*"
    r"([A-Za-z0-9_.+!-]+)"
    r")?"
)


IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "site-packages",
    "dist",
    "build",
    "uploads",
}


def _normalize_name(name: str) -> str:
    return re.sub(
        r"[-_.]+",
        "-",
        name,
    ).lower()


def _parse_requirement_line(
    line: str,
    source_file: str,
) -> PackageDependency | None:
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    if line.startswith(
        (
            "-r ",
            "--requirement ",
            "-c ",
            "--constraint ",
            "--index-url ",
            "--extra-index-url ",
            "--find-links ",
        )
    ):
        return None

    line = line.split(
        " #",
        1,
    )[0].strip()

    # Ignore environment markers for now.
    line = line.split(
        ";",
        1,
    )[0].strip()

    match = _REQUIREMENT_RE.match(line)

    if match is None:
        return None

    name = match.group(1)

    if not name:
        return None

    operator = match.group(2)
    version = match.group(3)

    normalized_version = None

    if operator and version:
        normalized_version = (
            f"{operator}{version}"
        )

    return PackageDependency(
        name=_normalize_name(name),
        version=normalized_version,
        source_file=source_file,
    )


def parse_requirements(
    source_file: str,
    text: str,
) -> list[PackageDependency]:
    dependencies = []

    for line in text.splitlines():
        dependency = _parse_requirement_line(
            line,
            source_file,
        )

        if dependency is not None:
            dependencies.append(
                dependency
            )

    return dependencies


def parse_pyproject(
    source_file: str,
    text: str,
) -> list[PackageDependency]:
    data = tomllib.loads(text)

    project = data.get(
        "project",
        {},
    )

    dependencies = []

    for requirement in project.get(
        "dependencies",
        [],
    ):
        dependency = _parse_requirement_line(
            requirement,
            source_file,
        )

        if dependency is not None:
            dependencies.append(
                dependency
            )

    optional = project.get(
        "optional-dependencies",
        {},
    )

    for requirements in optional.values():
        for requirement in requirements:
            dependency = _parse_requirement_line(
                requirement,
                source_file,
            )

            if dependency is not None:
                dependencies.append(
                    PackageDependency(
                        name=dependency.name,
                        version=dependency.version,
                        source_file=dependency.source_file,
                        dependency_type="optional",
                    )
                )

    return dependencies


def _is_ignored(path: Path) -> bool:
    return any(
        part in IGNORED_DIRECTORIES
        for part in path.parts
    )


def extract_dependencies(
    repository_root: str,
) -> list[PackageDependency]:
    root = Path(repository_root).resolve()

    dependencies = []

    for path in root.rglob(
        "requirements*.txt"
    ):
        relative = path.relative_to(root)

        if _is_ignored(relative):
            continue

        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except OSError:
            continue

        dependencies.extend(
            parse_requirements(
                str(relative),
                text,
            )
        )

    for path in root.rglob(
        "pyproject.toml"
    ):
        relative = path.relative_to(root)

        if _is_ignored(relative):
            continue

        try:
            text = path.read_text(
                encoding="utf-8"
            )
            parsed = parse_pyproject(
                str(relative),
                text,
            )
        except (
            OSError,
            ValueError,
        ):
            continue

        dependencies.extend(parsed)

    unique = {}

    for dependency in dependencies:
        key = (
            dependency.name,
            dependency.version,
            dependency.source_file,
            dependency.dependency_type,
        )
        unique[key] = dependency

    return list(unique.values())
