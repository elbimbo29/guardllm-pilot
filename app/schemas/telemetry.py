from pydantic import BaseModel, Field
from typing import Optional
import uuid


class TelemetryLogCreate(BaseModel):
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float
    status_code: int = 200
    guardrail_status: str = "PASSED"
    prompt_text: Optional[str] = ""
    response_text: Optional[str] = ""


class GuardrailEvaluationCreate(BaseModel):
    request_id: uuid.UUID
    evaluator_name: str
    score: float
    passed: bool
    reason: Optional[str] = ""
