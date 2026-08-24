from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from analyzer.core.rules.base import AnalysisRule


@dataclass(frozen=True, slots=True)
class RegisteredRule:
    """A rule registered with the IntelliReview rule registry."""

    rule_class: Type[AnalysisRule]
    enabled: bool = True


class RuleRegistry:
    """Central registry for IntelliReview analysis rules."""

    def __init__(self) -> None:
        self._rules: dict[str, RegisteredRule] = {}

    def register(
        self,
        rule_class: Type[AnalysisRule],
        *,
        enabled: bool = True,
    ) -> None:
        rule_id = rule_class.metadata.rule_id

        if rule_id in self._rules:
            raise ValueError(
                f"Rule already registered: {rule_id}"
            )

        self._rules[rule_id] = RegisteredRule(
            rule_class=rule_class,
            enabled=enabled,
        )

    def unregister(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def get(
        self,
        rule_id: str,
    ) -> Type[AnalysisRule]:
        try:
            return self._rules[rule_id].rule_class
        except KeyError:
            raise KeyError(
                f"Unknown rule: {rule_id}"
            ) from None

    def all(self) -> dict[str, RegisteredRule]:
        return dict(self._rules)

    def enabled(self) -> list[Type[AnalysisRule]]:
        return [
            registered.rule_class
            for registered in self._rules.values()
            if registered.enabled
        ]

    def create_rules(self) -> list[AnalysisRule]:
        return [
            rule_class()
            for rule_class in self.enabled()
        ]

    def enable(self, rule_id: str) -> None:
        registered = self._rules.get(rule_id)

        if registered is None:
            raise KeyError(f"Unknown rule: {rule_id}")

        self._rules[rule_id] = RegisteredRule(
            rule_class=registered.rule_class,
            enabled=True,
        )

    def disable(self, rule_id: str) -> None:
        registered = self._rules.get(rule_id)

        if registered is None:
            raise KeyError(f"Unknown rule: {rule_id}")

        self._rules[rule_id] = RegisteredRule(
            rule_class=registered.rule_class,
            enabled=False,
        )
