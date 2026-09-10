from datetime import datetime, timezone

from analyzer.baseline import build_baseline
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


def test_build_baseline_from_analysis_run():
    finding = Finding(
        rule_id="security.test",
        title="Hardcoded credential",
        description="Test finding",
        severity=Severity.HIGH,
        location=SourceLocation(
            file_path="app.py",
            line_start=10,
        ),
        analyzer="security",
    )

    now = datetime.now(timezone.utc)

    result = RepositoryAnalysisResult(
        analyzer_id="security",
        status=RepositoryAnalysisStatus.SUCCESS,
        started_at=now,
        completed_at=now,
        artifacts={"findings": (finding,)},
    )

    run = RepositoryAnalysisRun(
        repository_id="test-repo",
        revision="abc123",
        started_at=now,
        completed_at=now,
        results=(result,),
    )

    baseline = build_baseline(run)

    assert baseline.repository_id == "test-repo"
    assert baseline.revision == "abc123"
    assert len(baseline.findings) == 1
    assert baseline.findings[0].file_path == "app.py"
    assert baseline.findings[0].line_start == 10
    assert baseline.findings[0].fingerprint


def test_empty_analysis_creates_empty_baseline():
    now = datetime.now(timezone.utc)

    run = RepositoryAnalysisRun(
        repository_id="test-repo",
        revision="abc123",
        started_at=now,
        completed_at=now,
        results=(),
    )

    baseline = build_baseline(run)

    assert baseline.findings == ()
