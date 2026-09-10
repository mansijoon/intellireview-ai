from __future__ import annotations

from analyzer.baseline.fingerprint import finding_fingerprint
from analyzer.baseline.models import Baseline, BaselineFinding
from analyzer.core.repository_orchestrator import RepositoryAnalysisRun


def build_baseline(
    run: RepositoryAnalysisRun,
) -> Baseline:
    findings = tuple(
        BaselineFinding.from_finding(
            finding,
            finding_fingerprint(finding),
        )
        for finding in run.findings
    )

    return Baseline.create(
        repository_id=run.repository_id,
        revision=run.revision,
        repository_fingerprint=_repository_fingerprint(run),
        findings=findings,
    )


def _repository_fingerprint(
    run: RepositoryAnalysisRun,
) -> str:
    import hashlib

    payload = "\0".join(
        (
            run.repository_id,
            run.revision,
        )
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()
