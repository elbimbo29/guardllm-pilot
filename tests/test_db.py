import pytest

def is_db_available():
    try:
        from app.db import get_db_connection, release_db_connection
        conn = get_db_connection()
        release_db_connection(conn)
        return True
    except Exception:
        return False

@pytest.mark.skipif(not is_db_available(), reason="PostgreSQL/TimescaleDB is not running locally")
def test_log_llm_request_db():
    from app.services.telemetry import log_llm_request
    try:
        log_llm_request("req-test-01", "gpt-4o", 150, 50, 0.002, 120.5)
        assert True
    except Exception as e:
        pytest.fail(f"Database logging failed: {e}")
