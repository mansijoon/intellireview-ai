from datetime import datetime, timezone
from pathlib import Path

import pytest

from analyzer.baseline import (
    compare_current_run,
    create_baseline,
)
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)
from analyzer.core.models.repository_analysis import (
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_orchestrator import (
    RepositoryAnalysisRun,
)


def make_run(
    root: Path,
    revision: str,
    findings: tuple[Finding, ...],
) -> RepositoryAnalysisRun:
    now = datetime.now(timezone.utc)

    result = RepositoryAnalysisResult(
        analyzer_id="security",
        status=RepositoryAnalysisStatus.SUCCESS,
        started_at=now,
        completed_at=now,
        artifacts={"findings": findings},
    )

    return RepositoryAnalysisRun(
        repository_id="test-repo",
        revision=revision,
        started_at=now,
        completed_at=now,
        results=(result,),
    )


def make_finding(
    line: int,
    rule_id: str = "security.test",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        title="Test finding",
        description="Test",
        severity=Severity.HIGH,
        location=SourceLocation(
            file_path="app.py",
            line_start=line,
        ),
        analyzer="security",
    )


def test_compare_current_run(tmp_path: Path):
    baseline_finding = make_finding(10)

    create_baseline(
        make_run(
            tmp_path,
            "abc123",
            (baseline_finding,),
        ),
        str(tmp_path),
    )

    current = make_run(
        tmp_path,
        "def456",
        (
            baseline_finding,
            make_finding(
                20,
                "security.new",
            ),
        ),
    )

    comparison = compare_current_run(
        current,
        str(tmp_path),
    )

    assert comparison.baseline_revision == "abc123"
    assert comparison.current_revision == "def456"
    assert comparison.new_count == 1
    assert comparison.unchanged_count == 1
    assert comparison.resolved_count == 0
    assert comparison.has_regressions is True


def test_compare_requires_baseline(tmp_path: Path):
    run = make_run(
        tmp_path,
        "abc123",
        (),
    )

    with pytest.raises(FileNotFoundError):
        compare_current_run(
            run,
            str(tmp_path),
        )
