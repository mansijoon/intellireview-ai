from __future__ import annotations

from analyzer.ast_analyzer import analyze_ast
from analyzer.core.context import AnalysisContext
from analyzer.core.models import Finding
from analyzer.core.rules import AnalysisRule, RuleMetadata
from analyzer.core.rules.legacy import convert_legacy_findings


class ASTRule(AnalysisRule):
    """Expose the legacy AST analyzer through the canonical rule contract."""

    metadata = RuleMetadata(
        rule_id="AST-LEGACY",
        name="AST Analysis",
        description="Runs the existing IntelliReview AST analyzer.",
        category="static_analysis",
    )

    def analyze(
        self,
        context: AnalysisContext,
    ) -> list[Finding]:
        return convert_legacy_findings(
            analyze_ast(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="ast_rule",
            default_title="AST analysis finding",
        )
