from __future__ import annotations

from datetime import datetime, timezone

from analyzer.code_metrics import calculate_metrics
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
from analyzer.complexity.models import (
    ComplexityReport,
    FileComplexity,
)


SUPPORTED_LANGUAGES = {
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "java",
    "c",
    "cpp",
    "c++",
}


class ComplexityRepositoryAnalyzer(RepositoryAnalyzer):
    """Repository-wide deterministic complexity analysis."""

    metadata = RepositoryAnalyzerMetadata(
        analyzer_id="complexity",
        name="Complexity Analyzer",
        description=(
            "Computes repository-wide source complexity "
            "and structural metrics."
        ),
    )

    def analyze(
        self,
        repository: RepositoryContext,
    ) -> RepositoryAnalysisResult:
        started_at = datetime.now(timezone.utc)

        try:
            files: list[FileComplexity] = []

            for source_file in repository.files:
                if source_file.language.lower() not in SUPPORTED_LANGUAGES:
                    continue

                context = repository.get_context(
                    source_file.path
                )

                try:
                    metrics = calculate_metrics(
                        context.source
                    )
                except Exception:
                    continue

                files.append(
                    FileComplexity(
                        file_path=source_file.path,
                        language=source_file.language,
                        lines_of_code=int(
                            metrics.get(
                                "lines_of_code",
                                metrics.get("lines", 0),
                            )
                        ),
                        cyclomatic_complexity=int(
                            metrics.get(
                                "cyclomatic_complexity",
                                0,
                            )
                        ),
                        complexity_score=float(
                            metrics.get(
                                "complexity_score",
                                0,
                            )
                        ),
                        function_count=int(
                            metrics.get(
                                "functions",
                                0,
                            )
                        ),
                        class_count=int(
                            metrics.get(
                                "classes",
                                0,
                            )
                        ),
                        import_count=int(
                            metrics.get(
                                "imports",
                                0,
                            )
                        ),
                    )
                )

            total_lines = sum(
                item.lines_of_code
                for item in files
            )

            total_functions = sum(
                item.function_count
                for item in files
            )

            total_classes = sum(
                item.class_count
                for item in files
            )

            total_imports = sum(
                item.import_count
                for item in files
            )

            total_cyclomatic = sum(
                item.cyclomatic_complexity
                for item in files
            )

            average_complexity = (
                round(
                    total_cyclomatic / len(files),
                    2,
                )
                if files
                else 0.0
            )

            high_complexity_files = tuple(
                sorted(
                    (
                        item
                        for item in files
                        if item.cyclomatic_complexity >= 10
                    ),
                    key=lambda item: (
                        -item.cyclomatic_complexity,
                        item.file_path,
                    ),
                )
            )

            ordered_files = tuple(
                sorted(
                    files,
                    key=lambda item: (
                        -item.cyclomatic_complexity,
                        item.file_path,
                    ),
                )
            )

            report = ComplexityReport(
                file_count=len(files),
                total_lines=total_lines,
                total_functions=total_functions,
                total_classes=total_classes,
                total_imports=total_imports,
                total_cyclomatic_complexity=(
                    total_cyclomatic
                ),
                average_complexity=average_complexity,
                high_complexity_files=(
                    high_complexity_files
                ),
                files=ordered_files,
            )

            artifacts = {
                "complexity_report": report,
                "file_complexities": ordered_files,
                "file_count": report.file_count,
                "total_lines": report.total_lines,
                "total_functions": report.total_functions,
                "total_classes": report.total_classes,
                "total_imports": report.total_imports,
                "total_cyclomatic_complexity": (
                    report.total_cyclomatic_complexity
                ),
                "average_complexity": (
                    report.average_complexity
                ),
                "high_complexity_files": (
                    report.high_complexity_files
                ),
            }

            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                artifacts=artifacts,
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Complexity analysis completed "
                            "successfully."
                        ),
                        severity="info",
                    ),
                ),
            )

        except Exception as exc:
            result = RepositoryAnalysisResult(
                analyzer_id=self.metadata.analyzer_id,
                status=RepositoryAnalysisStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                diagnostics=(
                    AnalysisDiagnostic(
                        message=(
                            "Complexity analysis failed: "
                            f"{exc}"
                        ),
                        severity="error",
                    ),
                ),
            )

        repository.set_artifact(
            "complexity_analysis",
            result,
        )

        return result
