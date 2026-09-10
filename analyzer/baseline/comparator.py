from __future__ import annotations

from analyzer.baseline.models import (
    Baseline,
    BaselineComparison,
    BaselineFinding,
)


def compare_baseline(
    baseline: Baseline,
    current_findings: tuple[BaselineFinding, ...],
    *,
    current_revision: str,
) -> BaselineComparison:
    baseline_by_fingerprint = {
        finding.fingerprint: finding
        for finding in baseline.findings
    }

    current_by_fingerprint = {
        finding.fingerprint: finding
        for finding in current_findings
    }

    baseline_keys = set(
        baseline_by_fingerprint
    )
    current_keys = set(
        current_by_fingerprint
    )

    new_findings = tuple(
        current_by_fingerprint[key]
        for key in sorted(
            current_keys - baseline_keys
        )
    )

    resolved_findings = tuple(
        baseline_by_fingerprint[key]
        for key in sorted(
            baseline_keys - current_keys
        )
    )

    unchanged_findings = tuple(
        current_by_fingerprint[key]
        for key in sorted(
            baseline_keys & current_keys
        )
    )

    return BaselineComparison(
        repository_id=baseline.repository_id,
        baseline_revision=baseline.revision,
        current_revision=current_revision,
        new_findings=new_findings,
        resolved_findings=resolved_findings,
        unchanged_findings=unchanged_findings,
    )
