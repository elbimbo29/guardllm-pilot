import time
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.schemas.guardrails import GuardrailAction, EvaluationSummary
from app.services.guardrails.rules import PIIDetector, PromptInjectionDetector
from app.services.guardrails.engine import GuardrailEngine
from app.services.telemetry_async import save_guardrail_evaluation

app = FastAPI(title="GuardLLM Proxy Service", version="0.1.0")

guardrail_engine = GuardrailEngine(
    input_rules=[PIIDetector(), PromptInjectionDetector()]
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, background_tasks: BackgroundTasks
):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages payload cannot be empty.")

    request_id = f"req-{uuid.uuid4().hex[:12]}"
    user_message = request.messages[-1].content

    # Step 1: Run Guardrail Engine on Input
    eval_summary: EvaluationSummary = await guardrail_engine.evaluate_input(
        user_message
    )

    # Step 2: Queue Async Telemetry Persistence
    background_tasks.add_task(
        save_guardrail_evaluation, request_id, eval_summary, user_message
    )

    # Step 3: Handle BLOCK action
    if not eval_summary.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Request blocked by safety guardrails.",
                "action": eval_summary.overall_action,
                "execution_time_ms": eval_summary.execution_time_ms,
                "request_id": request_id,
            },
        )

    # Step 4: Handle MASK action
    processed_prompt = user_message
    if eval_summary.overall_action == GuardrailAction.MASK and eval_summary.masked_text:
        processed_prompt = eval_summary.masked_text

    response_content = f"Echo response for: '{processed_prompt}'"

    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_content},
                "finish_reason": "stop",
            }
        ],
        "guardrail_eval": {
            "action": eval_summary.overall_action,
            "execution_time_ms": eval_summary.execution_time_ms,
        },
    }
