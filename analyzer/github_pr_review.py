from __future__ import annotations

from dataclasses import dataclass

from analyzer.github_integration import GitHubClient


@dataclass(frozen=True, slots=True)
class PRFinding:
    path: str
    line: int
    message: str
    severity: str


def extract_added_lines(
    patch: str,
) -> list[tuple[int, str]]:
    results: list[tuple[int, str]] = []

    old_line = 0
    new_line = 0

    for raw_line in patch.splitlines():
        if raw_line.startswith("@@"):
            parts = raw_line.split()

            old_range = parts[1][1:]
            new_range = parts[2][1:]

            old_line = int(old_range.split(",")[0])
            new_line = int(new_range.split(",")[0])
            continue

        if raw_line.startswith("+++"):
            continue

        if raw_line.startswith("---"):
            continue

        if raw_line.startswith("+"):
            results.append(
                (new_line, raw_line[1:])
            )
            new_line += 1
            continue

        if raw_line.startswith("-"):
            old_line += 1
            continue

        old_line += 1
        new_line += 1

    return results


def build_pr_findings(
    files: list[dict],
) -> tuple[PRFinding, ...]:
    findings: list[PRFinding] = []

    for file in files:
        path = file.get("filename", "")
        patch = file.get("patch")

        if not path or not patch:
            continue

        for line_number, content in extract_added_lines(
            patch
        ):
            lowered = content.lower()

            if "password =" in lowered:
                findings.append(
                    PRFinding(
                        path=path,
                        line=line_number,
                        message=(
                            "Hardcoded credential detected. "
                            "Use secure configuration instead."
                        ),
                        severity="High",
                    )
                )

            if "print(" in lowered:
                findings.append(
                    PRFinding(
                        path=path,
                        line=line_number,
                        message=(
                            "Debug output detected in changed code."
                        ),
                        severity="Low",
                    )
                )

    return tuple(findings)


def publish_inline_findings(
    client: GitHubClient,
    owner: str,
    repository: str,
    pull_number: int,
    commit_id: str,
    findings: tuple[PRFinding, ...],
) -> int:
    published = 0

    for finding in findings:
        client.create_review_comment(
            owner,
            repository,
            pull_number,
            body=(
                f"**{finding.severity}**: "
                f"{finding.message}"
            ),
            commit_id=commit_id,
            path=finding.path,
            line=finding.line,
        )

        published += 1

    return published

def publish_pr_review(
    client: GitHubClient,
    owner: str,
    repository: str,
    pull_number: int,
    commit_id: str,
    files: list[dict],
) -> int:
    findings = build_pr_findings(files)

    if not findings:
        return 0

    return publish_inline_findings(
        client,
        owner,
        repository,
        pull_number,
        commit_id,
        findings,
    )

def build_pr_summary(
    findings: tuple[PRFinding, ...],
) -> str:
    if not findings:
        return "## IntelliReview\n\nNo findings detected."

    counts: dict[str, int] = {}

    for finding in findings:
        counts[finding.severity] = (
            counts.get(finding.severity, 0) + 1
        )

    lines = [
        "## IntelliReview",
        "",
        f"**Findings:** {len(findings)}",
        "",
        "### Severity Summary",
    ]

    for severity in (
        "Critical",
        "High",
        "Medium",
        "Low",
    ):
        count = counts.get(severity, 0)
        if count:
            lines.append(f"- **{severity}:** {count}")

    lines.extend(
        (
            "",
            "### Findings",
        )
    )

    for finding in findings:
        lines.append(
            f"- **{finding.severity}** "
            f"`{finding.path}:{finding.line}` — "
            f"{finding.message}"
        )

    return "\n".join(lines)

def review_and_publish_pr(
    client: GitHubClient,
    owner: str,
    repository: str,
    pull_number: int,
    commit_id: str,
    files: list[dict],
) -> tuple[int, str]:
    findings = build_pr_findings(files)

    summary = build_pr_summary(findings)

    published = publish_inline_findings(
        client,
        owner,
        repository,
        pull_number,
        commit_id,
        findings,
    )

    return published, summary

