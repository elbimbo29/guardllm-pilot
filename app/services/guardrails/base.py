# app/services/guardrails/base.py
from abc import ABC, abstractmethod
from app.schemas.guardrails import RuleResult


class BaseGuardrail(ABC):
    def __init__(self, rule_id: str, rule_name: str):
        self.rule_id = rule_id
        self.rule_name = rule_name

    @abstractmethod
    async def evaluate(self, text: str) -> RuleResult:
        """Evaluate input or output text against the specific guardrail rule."""
        pass
