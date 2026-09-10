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


def _finding_line(
    finding: dict,
    patch: str,
) -> int:
    """
    Best-effort mapping of a deterministic finding back to a
    changed PR line.

    Findings without an explicit source line are mapped to the
    first added source line.
    """

    explicit_line = finding.get("line")

    if isinstance(explicit_line, int):
        return explicit_line

    added_lines = extract_added_lines(patch)

    if added_lines:
        return added_lines[0][0]

    return 1


def build_pr_findings(
    files: list[dict],
) -> tuple[PRFinding, ...]:
    """
    Run the canonical IntelliReview PR engine against changed files.
    """

    from analyzer.pr_review import review_pull_request_files

    findings = review_pull_request_files(files)

    result: list[PRFinding] = []

    for finding in findings:
        path = finding.get("file_path", "")

        if not path:
            continue

        source_file = next(
            (
                file
                for file in files
                if file.get("filename") == path
            ),
            None,
        )

        if source_file is None:
            continue

        line = _finding_line(
            finding,
            source_file.get("patch", ""),
        )

        message = finding.get(
            "message",
            finding.get("type", "IntelliReview finding"),
        )

        severity = finding.get(
            "severity",
            "Medium",
        )

        result.append(
            PRFinding(
                path=path,
                line=line,
                message=message,
                severity=severity,
            )
        )

    return tuple(result)


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
            lines.append(
                f"- **{severity}:** {count}"
            )

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
    """
    Canonical end-to-end GitHub PR review path.

    Changed GitHub files are analyzed by IntelliReview's
    deterministic PR engine, converted into GitHub findings,
    published inline, and summarized.
    """

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


def review_github_pr_files(
    files: list[dict],
) -> tuple[list[dict], str]:
    """
    Return raw IntelliReview findings and a PR summary.
    """

    from analyzer.pr_review import review_pull_request_files

    findings = review_pull_request_files(files)

    if not findings:
        return [], "## IntelliReview\n\nNo findings detected."

    counts: dict[str, int] = {}

    for finding in findings:
        severity = finding.get(
            "severity",
            "Unknown",
        )

        counts[severity] = counts.get(
            severity,
            0,
        ) + 1

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
            lines.append(
                f"- **{severity}:** {count}"
            )

    lines.extend(
        (
            "",
            "### Findings",
        )
    )

    for finding in findings:
        path = finding.get(
            "file_path",
            "<unknown>",
        )

        message = finding.get(
            "message",
            finding.get(
                "type",
                "Finding",
            ),
        )

        lines.append(
            f"- **{finding.get('severity', 'Unknown')}** "
            f"`{path}` — {message}"
        )

    return findings, "\n".join(lines)
