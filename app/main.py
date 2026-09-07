import os
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.schemas.guardrails import GuardrailAction, EvaluationSummary
from app.services.guardrails.rules import PIIDetector, PromptInjectionDetector
from app.services.guardrails.engine import GuardrailEngine
from app.services.telemetry_async import save_guardrail_evaluation

# Step 1: Read Redis URL from environment (fallback to localhost for local dev)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Step 2: Initialize Slowapi Limiter backed by Redis
limiter = Limiter(
    key_func=get_remote_address, storage_uri=REDIS_URL, default_limits=["100/minute"]
)

app = FastAPI(title="GuardLLM Proxy Service", version="0.1.0")

# Step 3: Attach limiter and RateLimitExceeded handler to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("60/minute")  # Step 4: Restrict IP to 60 requests/min
async def chat_completions(
    request: Request, body: ChatCompletionRequest, background_tasks: BackgroundTasks
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="Messages payload cannot be empty.")

    request_id = f"req-{uuid.uuid4().hex[:12]}"
    user_message = body.messages[-1].content

    # Step 1: Run Guardrail Engine on Input
    eval_summary: EvaluationSummary = await guardrail_engine.evaluate_input(
        user_message
    )

    # Step 2: Handle BLOCK action
    if not eval_summary.passed:
        # Await telemetry directly before throwing HTTPException,
        # as FastAPI discards background_tasks when an exception is raised.
        await save_guardrail_evaluation(request_id, eval_summary, user_message)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Request blocked by safety guardrails.",
                "action": (
                    eval_summary.overall_action.value
                    if hasattr(eval_summary.overall_action, "value")
                    else eval_summary.overall_action
                ),
                "execution_time_ms": eval_summary.execution_time_ms,
                "request_id": request_id,
            },
        )

    # Step 3: Queue Async Telemetry Persistence for successful (PASS / MASK) requests
    background_tasks.add_task(
        save_guardrail_evaluation, request_id, eval_summary, user_message
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
        "model": body.model,
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
