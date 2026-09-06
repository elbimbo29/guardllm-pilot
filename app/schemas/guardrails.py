from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GuardrailAction(str, Enum):
    PASS = "PASS"
    FLAG = "FLAG"
    BLOCK = "BLOCK"
    MASK = "MASK"


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    action: GuardrailAction
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationSummary(BaseModel):
    overall_action: GuardrailAction
    passed: bool
    input_results: List[RuleResult] = Field(default_factory=list)
    output_results: List[RuleResult] = Field(default_factory=list)
    masked_text: Optional[str] = None
    execution_time_ms: float = 0.0
