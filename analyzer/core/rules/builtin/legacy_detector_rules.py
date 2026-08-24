from __future__ import annotations

from analyzer.core.context import AnalysisContext
from analyzer.core.models import Finding
from analyzer.core.rules import AnalysisRule, RuleMetadata
from analyzer.core.rules.legacy import convert_legacy_findings

from analyzer.secret_detector import detect_secrets
from analyzer.duplicate_detector import detect_duplicate_functions
from analyzer.unused_import_detector import detect_unused_imports
from analyzer.unused_variable_detector import detect_unused_variables
from analyzer.dead_function_detector import detect_dead_functions


class SecretDetectionRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="SEC-SECRET-001",
        name="Secret Detection",
        description="Detects potentially hardcoded secrets and credentials.",
        category="security",
    )

    def analyze(self, context: AnalysisContext) -> list[Finding]:
        return convert_legacy_findings(
            detect_secrets(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="secret_detection",
            default_title="Potential secret detected",
        )


class DuplicateFunctionRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PY-DUP-001",
        name="Duplicate Function",
        description="Detects duplicate Python function bodies.",
        category="maintainability",
    )

    def analyze(self, context: AnalysisContext) -> list[Finding]:
        return convert_legacy_findings(
            detect_duplicate_functions(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="duplicate_function",
            default_title="Duplicate function",
        )


class LegacyUnusedImportRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PY-IMPORT-LEGACY-001",
        name="Legacy Unused Import Detection",
        description="Runs the existing unused-import detector.",
        category="maintainability",
    )

    def analyze(self, context: AnalysisContext) -> list[Finding]:
        return convert_legacy_findings(
            detect_unused_imports(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="unused_import_legacy",
            default_title="Unused import",
        )


class LegacyUnusedVariableRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PY-VAR-LEGACY-001",
        name="Legacy Unused Variable Detection",
        description="Runs the existing unused-variable detector.",
        category="maintainability",
    )

    def analyze(self, context: AnalysisContext) -> list[Finding]:
        return convert_legacy_findings(
            detect_unused_variables(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="unused_variable_legacy",
            default_title="Unused variable",
        )


class DeadFunctionRule(AnalysisRule):
    metadata = RuleMetadata(
        rule_id="PY-DEAD-001",
        name="Dead Function",
        description="Detects Python functions that appear to be unused.",
        category="maintainability",
    )

    def analyze(self, context: AnalysisContext) -> list[Finding]:
        return convert_legacy_findings(
            detect_dead_functions(context.source),
            context,
            rule_id=self.metadata.rule_id,
            analyzer="dead_function",
            default_title="Dead function",
        )
