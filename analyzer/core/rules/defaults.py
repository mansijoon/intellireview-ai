from __future__ import annotations

from analyzer.core.rules import RuleRegistry
from analyzer.core.rules.builtin import (
    ASTRule,
    DeadFunctionRule,
    DuplicateFunctionRule,
    LegacyUnusedImportRule,
    LegacyUnusedVariableRule,
    SecretDetectionRule,
    DangerousEvalExecRule,
    ShellCommandExecutionRule,
    SubprocessShellTrueRule,
    UnsafeDeserializationRule,
    WeakCryptographyRule,
    UnusedImportRule,
    UnusedVariableRule,
)


def create_default_registry() -> RuleRegistry:
    """Create the standard IntelliReview deterministic rule registry."""

    registry = RuleRegistry()

    registry.register(ASTRule)

    registry.register(UnusedImportRule)
    registry.register(UnusedVariableRule)

    registry.register(LegacyUnusedImportRule)
    registry.register(LegacyUnusedVariableRule)

    registry.register(DuplicateFunctionRule)
    registry.register(DeadFunctionRule)
    registry.register(SecretDetectionRule)
    registry.register(DangerousEvalExecRule)
    registry.register(ShellCommandExecutionRule)
    registry.register(SubprocessShellTrueRule)
    registry.register(UnsafeDeserializationRule)
    registry.register(WeakCryptographyRule)

    return registry
