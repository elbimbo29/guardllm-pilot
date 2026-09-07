import os
import time
import uuid
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.schemas.guardrails import EvaluationSummary, GuardrailAction
from app.services.guardrails.engine import GuardrailEngine
from app.services.guardrails.rules import PIIDetector, PromptInjectionDetector
from app.services.telemetry_async import save_guardrail_evaluation

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL,
    default_limits=["60/minute"],
)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

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
@limiter.limit("60/minute")
async def chat_completions(
    request: Request, body: ChatCompletionRequest, background_tasks: BackgroundTasks
):
    if not body.messages:
        return JSONResponse(
            status_code=400,
            content={"detail": "Messages payload cannot be empty."},
        )

    request_id = f"req-{uuid.uuid4().hex[:12]}"
    user_message = body.messages[-1].content

    # Step 1: Run Guardrail Engine
    eval_summary: EvaluationSummary = await guardrail_engine.evaluate_input(
        user_message
    )

    # Step 2: Queue Telemetry Persistence for ALL requests in BackgroundTasks
    # BackgroundTasks execute AFTER the JSONResponse is returned to the client
    background_tasks.add_task(
        save_guardrail_evaluation, request_id, eval_summary, user_message
    )

    # Step 3: Handle BLOCK action using JSONResponse instead of HTTPException
    if not eval_summary.passed:
        action_val = (
            eval_summary.overall_action.value
            if hasattr(eval_summary.overall_action, "value")
            else eval_summary.overall_action
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "Request blocked by safety guardrails.",
                "action": action_val,
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
