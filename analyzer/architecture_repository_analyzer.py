from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone

from analyzer.core.analyzers import (
    RepositoryAnalyzer,
    RepositoryAnalyzerMetadata,
)
from analyzer.core.models import (
    AnalysisDiagnostic,
    RepositoryAnalysisResult,
    RepositoryAnalysisStatus,
)
from analyzer.core.repository_context import RepositoryContext


class ArchitectureRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide architectural analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="architecture",
            depends_on=frozenset({"dependency"}),
        source_sensitive=True,
        name="Architecture Analyzer",
        description=(
            "Analyzes repository and module structure, "
            "detecting oversized repositories, large modules, "
            "and god modules."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        findings: list[dict] = []
        module_statistics: dict[str, dict[str, int]] = {}

        try:
            python_files = [
                source_file
                for source_file in repository.files
                if source_file.language == "python"
            ]

            total_modules = len(python_files)

            if total_modules > 100:
                findings.append(
                    {
                        "type": "Large Repository",
                        "severity": "Medium",
                        "message": (
                            f"Repository contains "
                            f"{total_modules} Python modules."
                        ),
                    }
                )

            for source_file in python_files:
                context = repository.get_context(
                    source_file.path
                )

                tree = context.ast_tree

                if tree is None:
                    diagnostics_message = (
                        f"Unable to parse {source_file.path}."
                    )

                    continue

                line_count = context.line_count

                function_count = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(
                        node,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                        ),
                    )
                )

                class_count = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(
                        node,
                        ast.ClassDef,
                    )
                )

                module_statistics[source_file.path] = {
                    "line_count": line_count,
                    "function_count": function_count,
                    "class_count": class_count,
                }

                if line_count > 300:
                    findings.append(
                        {
                            "type": "Large Module",
                            "severity": "Medium",
                            "file": source_file.path,
                            "message": (
                                f"{source_file.path} has "
                                f"{line_count} lines."
                            ),
                        }
                    )

                if (
                    line_count > 500
                    or function_count > 20
                    or class_count > 10
                ):
                    findings.append(
                        {
                            "type": "God Module",
                            "severity": "High",
                            "file": source_file.path,
                            "message": (
                                f"{source_file.path} has "
                                f"{line_count} lines, "
                                f"{function_count} functions, "
                                f"{class_count} classes."
                            ),
                        }
                    )

            score = calculate_architecture_score(
                findings,
                total_modules,
            )

            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="architecture",
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=completed_at,
                artifacts={
                    "architecture_findings": findings,
                    "architecture_score": score,
                    "total_modules": total_modules,
                    "module_statistics": module_statistics,
                    "finding_counts": dict(
                        Counter(
                            finding["type"]
                            for finding in findings
                        )
                    ),
                },
                diagnostics=(),
            )

            repository.set_artifact(
                "architecture_analysis",
                result,
            )

            return result

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            result = RepositoryAnalysisResult(
                analyzer_id="architecture",
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Architecture analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

            repository.set_artifact(
                "architecture_analysis",
                result,
            )

            return result


def calculate_architecture_score(
    findings: list[dict],
    total_modules: int,
) -> int:
    """Calculate an architecture score normalized by module count."""

    if total_modules <= 0:
        return 100

    weights = {
        "God Module": 40,
        "Large Module": 25,
        "Large Repository": 10,
    }

    counts = Counter(
        finding["type"]
        for finding in findings
    )

    penalty = 0.0

    for finding_type, weight in weights.items():
        ratio = (
            counts.get(finding_type, 0)
            / total_modules
        )

        penalty += ratio * weight

    score = round(100 - penalty)

    return max(
        0,
        min(100, score),
    )
