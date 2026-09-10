from datetime import datetime, timezone
from pathlib import Path

from analyzer.baseline import (
    create_baseline,
    load_baseline,
)
from analyzer.core.repository_orchestrator import (
    RepositoryAnalysisRun,
)


def test_create_and_load_baseline(tmp_path: Path):
    now = datetime.now(timezone.utc)

    run = RepositoryAnalysisRun(
        repository_id="test-repo",
        revision="abc123",
        started_at=now,
        completed_at=now,
        results=(),
    )

    baseline = create_baseline(run, str(tmp_path))

    assert baseline.repository_id == "test-repo"
    assert baseline.revision == "abc123"

    loaded = load_baseline(str(tmp_path))

    assert loaded == baseline
