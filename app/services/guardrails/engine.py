import time
from typing import List, Optional
from app.schemas.guardrails import GuardrailAction, RuleResult, EvaluationSummary
from app.services.guardrails.base import BaseGuardrail


class GuardrailEngine:
    def __init__(self, input_rules: Optional[List[BaseGuardrail]] = None):
        self.input_rules: List[BaseGuardrail] = input_rules or []

    async def evaluate_input(self, text: str) -> EvaluationSummary:
        start_time = time.perf_counter()
        results: List[RuleResult] = []
        overall_action = GuardrailAction.PASS
        masked_text: Optional[str] = None

        for rule in self.input_rules:
            res = await rule.evaluate(text)
            results.append(res)

            if res.action == GuardrailAction.BLOCK:
                overall_action = GuardrailAction.BLOCK
            elif res.action == GuardrailAction.MASK:
                if overall_action != GuardrailAction.BLOCK:
                    overall_action = GuardrailAction.MASK
                if "masked_text" in res.details:
                    masked_text = res.details["masked_text"]

        exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return EvaluationSummary(
            passed=(overall_action != GuardrailAction.BLOCK),
            overall_action=overall_action,
            execution_time_ms=exec_time_ms,
            input_results=results,
            output_results=[],
            masked_text=masked_text if overall_action == GuardrailAction.MASK else None,
        )
