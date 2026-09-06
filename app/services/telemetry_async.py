import json
import logging
from typing import Optional
from app.schemas.guardrails import EvaluationSummary

logger = logging.getLogger(__name__)

async def save_guardrail_evaluation(
    request_id: str,
    eval_summary: EvaluationSummary,
    raw_prompt: Optional[str] = None
) -> None:
    """
    Asynchronously persists guardrail evaluation results to TimescaleDB.
    Fails gracefully if the database is offline.
    """
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            results_payload = [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "action": r.action,
                    "score": r.score,
                    "details": r.details,
                }
                for r in eval_summary.results
            ]

            query = text("""
                INSERT INTO guardrail_evaluations (
                    request_id,
                    passed,
                    overall_action,
                    execution_time_ms,
                    rule_results
                ) VALUES (:request_id, :passed, :overall_action, :execution_time_ms, :rule_results);
            """)

            await session.execute(
                query,
                {
                    "request_id": request_id,
                    "passed": eval_summary.passed,
                    "overall_action": eval_summary.overall_action.value if hasattr(eval_summary.overall_action, 'value') else eval_summary.overall_action,
                    "execution_time_ms": eval_summary.execution_time_ms,
                    "rule_results": json.dumps(results_payload),
                },
            )
            await session.commit()
    except Exception as e:
        logger.warning(f"Could not persist guardrail evaluation (DB offline or unconfigured): {e}")
