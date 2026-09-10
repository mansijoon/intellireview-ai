from analyzer.baseline import (
    Baseline,
    BaselineFinding,
    BaselineStore,
    compare_baseline,
    finding_fingerprint,
)
from analyzer.core.models import (
    Finding,
    Severity,
    SourceLocation,
)


def make_finding(
    *,
    line: int,
    rule_id: str = "security.test",
    title: str = "Hardcoded credential",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        description="Test finding",
        severity=Severity.HIGH,
        location=SourceLocation(
            file_path="app.py",
            line_start=line,
        ),
        analyzer="security",
    )


def make_baseline_finding(
    finding: Finding,
) -> BaselineFinding:
    return BaselineFinding.from_finding(
        finding,
        finding_fingerprint(finding),
    )


def test_fingerprint_survives_line_movement():
    first = make_finding(line=10)
    second = make_finding(line=50)

    assert finding_fingerprint(first) == (
        finding_fingerprint(second)
    )


def test_different_rules_have_different_fingerprints():
    first = make_finding(
        line=10,
        rule_id="security.one",
    )

    second = make_finding(
        line=10,
        rule_id="security.two",
    )

    assert finding_fingerprint(first) != (
        finding_fingerprint(second)
    )


def test_baseline_comparison():
    unchanged = make_baseline_finding(
        make_finding(line=10)
    )

    resolved = make_baseline_finding(
        make_finding(
            line=20,
            rule_id="security.resolved",
        )
    )

    new = make_baseline_finding(
        make_finding(
            line=30,
            rule_id="security.new",
        )
    )

    baseline = Baseline.create(
        repository_id="repo",
        revision="baseline",
        repository_fingerprint="abc",
        findings=(
            unchanged,
            resolved,
        ),
    )

    comparison = compare_baseline(
        baseline,
        (
            unchanged,
            new,
        ),
        current_revision="current",
    )

    assert comparison.new_count == 1
    assert comparison.resolved_count == 1
    assert comparison.unchanged_count == 1
    assert comparison.has_regressions


def test_baseline_store(tmp_path):
    baseline = Baseline.create(
        repository_id="repo",
        revision="main",
        repository_fingerprint="abc123",
        findings=(),
    )

    store = BaselineStore(str(tmp_path))

    assert not store.exists()
    assert store.load() is None

    store.save(baseline)

    assert store.exists()

    loaded = store.load()

    assert loaded is not None
    assert loaded.repository_id == "repo"
    assert loaded.revision == "main"
    assert loaded.repository_fingerprint == "abc123"


def test_fingerprint_ignores_line_movement():
    first = make_finding(line=10)
    second = make_finding(line=50)

    assert finding_fingerprint(first) == finding_fingerprint(second)


def test_fingerprint_does_not_depend_on_repository_root(tmp_path):
    first = make_finding(line=10)

    assert finding_fingerprint(first) == finding_fingerprint(first)


def test_fingerprint_changes_for_different_files():
    first = Finding(
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

    second = Finding(
        rule_id="security.test",
        title="Hardcoded credential",
        description="Test finding",
        severity=Severity.HIGH,
        location=SourceLocation(
            file_path="other.py",
            line_start=10,
        ),
        analyzer="security",
    )

    assert finding_fingerprint(first) != (
        finding_fingerprint(second)
    )
