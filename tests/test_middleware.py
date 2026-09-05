import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db_connection

client = TestClient(app)


def test_chat_completions_telemetry_integration():
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Explain middleware in FastAPI."}],
    }

    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200

    data = response.json()
    request_id = data["id"]

    # Verify background execution wrote the request entry into TimescaleDB
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT model, status_code FROM llm_requests WHERE request_id = %s;",
                (request_id,),
            )
            row = cur.fetchone()

    assert row is not None
    assert row[0] == "gpt-4o-mini"
    assert row[1] == 200
