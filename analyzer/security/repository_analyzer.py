from __future__ import annotations

from datetime import datetime, timezone

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    Finding,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext
from analyzer.core.rules.defaults import create_default_registry

from analyzer.security.models import (
    SecurityAnalysisReport,
    SecurityCategory,
    SecurityFinding,
    SecurityRiskReport,
    SecuritySeverity,
    SecurityVerificationStatus,
)


class SecurityRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic security analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="security",
            depends_on=frozenset({"static"}),
        source_sensitive=False,
        name="Security Analyzer",
        description=(
            "Runs repository security rules and produces "
            "structured security findings and risk metadata."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            registry = create_default_registry()

            rules = [
                rule
                for rule in registry.create_rules()
                if rule.metadata.category == "security"
            ]

            findings: list[Finding] = []

            for rule in rules:
                for context in repository.iter_contexts():
                    findings.extend(
                        rule.analyze(context)
                    )

            security_findings: list[SecurityFinding] = []

            for finding in findings:
                severity_value = (
                    finding.severity.value
                    if hasattr(finding.severity, "value")
                    else str(finding.severity)
                ).lower()

                try:
                    severity = SecuritySeverity(
                        severity_value
                    )
                except ValueError:
                    severity = SecuritySeverity.MEDIUM

                security_findings.append(
                    SecurityFinding(
                        rule_id=finding.rule_id,
                        category=SecurityCategory.SAST,
                        severity=severity,
                        confidence=finding.confidence,
                        verification_status=(
                            SecurityVerificationStatus.UNVERIFIED
                        ),
                    )
                )

            severity_counts: dict[str, int] = {}

            for finding in security_findings:
                severity_counts[finding.severity.value] = (
                    severity_counts.get(
                        finding.severity.value,
                        0,
                    )
                    + 1
                )

            affected_files = {
                finding.location.file_path
                for finding in findings
            }

            report = SecurityAnalysisReport(
                file_count=repository.file_count,
                finding_count=len(findings),
                affected_file_count=len(affected_files),
                findings=security_findings,
            )

            verified_count = sum(
                finding.verification_status
                == SecurityVerificationStatus.VERIFIED
                for finding in security_findings
            )

            unverified_count = len(
                security_findings
            ) - verified_count

            risk_report = SecurityRiskReport(
                score=self._calculate_risk_score(
                    severity_counts
                ),
                severity_counts=severity_counts,
                verified_count=verified_count,
                unverified_count=unverified_count,
                finding_count=len(findings),
            )

            report.risk_report = risk_report

            artifacts = {
                "security_report": report,
                "findings": tuple(findings),
                "security_findings": tuple(
                    security_findings
                ),
                "finding_count": len(findings),
                "affected_file_count": len(
                    affected_files
                ),
                "security_percentage": (
                    (
                        len(affected_files)
                        / repository.file_count
                        * 100.0
                    )
                    if repository.file_count
                    else 0.0
                ),
                "severity_counts": severity_counts,
                "rule_count": len(rules),
                "risk_report": risk_report,
                "security_risk_score": risk_report.score,
            }

            result = RepositoryAnalysisResult(
                analyzer_id="security",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Security analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

            repository.set_artifact(
                "security_analysis",
                result,
            )

            return result

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id="security",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Security analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "security_analysis",
                result,
            )

            return result

    @staticmethod
    def _calculate_risk_score(
        severity_counts: dict[str, int],
    ) -> float:
        weights = {
            "critical": 25,
            "high": 15,
            "medium": 7,
            "low": 2,
        }

        raw_score = sum(
            weights.get(
                severity,
                0,
            )
            * count
            for severity, count in severity_counts.items()
        )

        return min(
            100.0,
            float(raw_score),
        )
