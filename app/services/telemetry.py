from datetime import datetime, timezone
import uuid
from typing import Optional
from app.db import get_db_connection


def log_llm_request(
    request_id: uuid.UUID,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    status_code: int,
    guardrail_status: str = "PASSED",
    prompt_text: Optional[str] = "",
    response_text: Optional[str] = "",
) -> None:
    """Inserts an API proxy request record into the llm_requests hypertable."""
    query = """
    INSERT INTO llm_requests (
        time, request_id, model, prompt_tokens, completion_tokens, 
        total_tokens, latency_ms, status_code, guardrail_status, 
        prompt_text, response_text
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    now = datetime.now(timezone.utc)
    total_tokens = prompt_tokens + completion_tokens

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    now,
                    str(request_id),
                    model,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    latency_ms,
                    status_code,
                    guardrail_status,
                    prompt_text,
                    response_text,
                ),
            )


def log_guardrail_evaluation(
    request_id: uuid.UUID,
    evaluator_name: str,
    score: float,
    passed: bool,
    reason: Optional[str] = "",
) -> None:
    """Inserts a guardrail evaluation record into the guardrail_evaluations hypertable."""
    query = """
    INSERT INTO guardrail_evaluations (
        time, request_id, evaluator_name, score, passed, reason
    ) VALUES (%s, %s, %s, %s, %s, %s);
    """
    now = datetime.now(timezone.utc)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    now,
                    str(request_id),
                    evaluator_name,
                    score,
                    passed,
                    reason,
                ),
            )
