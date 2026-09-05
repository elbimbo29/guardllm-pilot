import time
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional


from app.schemas.telemetry import TelemetryLogCreate, GuardrailEvaluationCreate
from app.services.telemetry_async import (
    record_telemetry_background,
    record_evaluation_background,
)

app = FastAPI(title="GuardLLM Proxy")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7


class ChatCompletionResponse(BaseModel):
    # Pass uuid.uuid4 directly to default_factory, and cast in usage if needed, or use uuid.UUID type:
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model: str
    choices: List[dict]
    usage: dict


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
):
    start_time = time.perf_counter()
    request_id = uuid.uuid4()

    # Concatenate prompt messages for telemetry logging
    prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

    # Simulated LLM response execution (to be replaced with actual upstream proxy call)
    response_text = f"Simulated proxy response for prompt in model {request.model}"
    prompt_tokens = len(prompt_text.split())
    completion_tokens = len(response_text.split())

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 1. Dispatch Request Telemetry DB Write in Background
    telemetry_log = TelemetryLogCreate(
        request_id=request_id,
        model=request.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        status_code=200,
        guardrail_status="PASSED",
        prompt_text=prompt_text,
        response_text=response_text,
    )
    record_telemetry_background(background_tasks, telemetry_log)

    # 2. Dispatch Sample Guardrail Evaluation Log in Background
    eval_log = GuardrailEvaluationCreate(
        request_id=request_id,
        evaluator_name="basic_length_check",
        score=1.0,
        passed=True,
        reason="Prompt length within threshold",
    )
    record_evaluation_background(background_tasks, eval_log)

    return ChatCompletionResponse(
        id=str(request_id),
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }
        ],
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    )
