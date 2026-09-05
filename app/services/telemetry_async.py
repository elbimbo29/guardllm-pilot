from fastapi import BackgroundTasks
from app.schemas.telemetry import TelemetryLogCreate, GuardrailEvaluationCreate
from app.services.telemetry import log_llm_request, log_guardrail_evaluation


def record_telemetry_background(
    background_tasks: BackgroundTasks, log_data: TelemetryLogCreate
) -> None:
    """Schedules the telemetry DB write to run asynchronously after response dispatch."""
    background_tasks.add_task(
        log_llm_request,
        request_id=log_data.request_id,
        model=log_data.model,
        prompt_tokens=log_data.prompt_tokens,
        completion_tokens=log_data.completion_tokens,
        latency_ms=log_data.latency_ms,
        status_code=log_data.status_code,
        guardrail_status=log_data.guardrail_status,
        prompt_text=log_data.prompt_text,
        response_text=log_data.response_text,
    )


def record_evaluation_background(
    background_tasks: BackgroundTasks, eval_data: GuardrailEvaluationCreate
) -> None:
    """Schedules a guardrail evaluation DB write asynchronously."""
    background_tasks.add_task(
        log_guardrail_evaluation,
        request_id=eval_data.request_id,
        evaluator_name=eval_data.evaluator_name,
        score=eval_data.score,
        passed=eval_data.passed,
        reason=eval_data.reason,
    )
