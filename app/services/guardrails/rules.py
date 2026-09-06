import re
from typing import Dict, List
from app.schemas.guardrails import GuardrailAction, RuleResult
from app.services.guardrails.base import BaseGuardrail


class PIIDetector(BaseGuardrail):
    def __init__(self):
        super().__init__(rule_id="rule_pii_001", rule_name="PII Detector")
        self.patterns: Dict[str, str] = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
        }

    async def evaluate(self, text: str) -> RuleResult:
        found_matches: List[Dict[str, str]] = []
        masked_text = text

        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    found_matches.append({"type": pii_type, "match": match})
                masked_text = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", masked_text)

        if found_matches:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                action=GuardrailAction.MASK,
                score=1.0,
                details={
                    "detected_pii": found_matches,
                    "masked_text": masked_text,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            action=GuardrailAction.PASS,
            score=0.0,
            details={},
        )


class PromptInjectionDetector(BaseGuardrail):
    def __init__(self):
        super().__init__(rule_id="rule_inj_001", rule_name="Prompt Injection Detector")
        self.injection_keywords = [
            "ignore previous instructions",
            "ignore all prior instructions",
            "system override",
            "you are now dan",
            "jailbreak",
            "disregard safety guidelines",
        ]

    async def evaluate(self, text: str) -> RuleResult:
        lowered = text.lower()
        matched = [kw for kw in self.injection_keywords if kw in lowered]

        if matched:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                action=GuardrailAction.BLOCK,
                score=0.95,
                details={"matched_keywords": matched},
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            action=GuardrailAction.PASS,
            score=0.0,
            details={},
        )
