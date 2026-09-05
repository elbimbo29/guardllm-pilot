import uuid
from app.services.telemetry import log_llm_request, log_guardrail_evaluation
from app.db import get_db_connection


def test_log_llm_request_and_verify():
    """Test inserting and retrieving a telemetry record from TimescaleDB."""
    test_id = uuid.uuid4()
    model_name = "test-gpt-4o"

    # Insert log entry
    log_llm_request(
        request_id=test_id,
        model=model_name,
        prompt_tokens=10,
        completion_tokens=20,
        latency_ms=150.5,
        status_code=200,
        guardrail_status="PASSED",
        prompt_text="Hello world",
        response_text="Hello! How can I help you?",
    )

    # Verify log entry in DB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT model, total_tokens FROM llm_requests WHERE request_id = %s;",
                (str(test_id),),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] == model_name
    assert row[1] == 30  # total_tokens = 10 + 20


def test_log_guardrail_evaluation():
    """Test inserting a guardrail evaluation record."""
    test_id = uuid.uuid4()

    log_guardrail_evaluation(
        request_id=test_id,
        evaluator_name="pii_scanner",
        score=0.99,
        passed=True,
        reason="No PII detected",
    )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT evaluator_name, passed FROM guardrail_evaluations WHERE request_id = %s;",
                (str(test_id),),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] == "pii_scanner"
    assert row[1] is True
