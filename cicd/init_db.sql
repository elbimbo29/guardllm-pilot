-- TimescaleDB Initialization Schema
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS llm_telemetry (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id VARCHAR(64) NOT NULL,
    prompt_length INT,
    response_length INT,
    latency_ms DOUBLE PRECISION,
    hallucination_score DOUBLE PRECISION,
    passed BOOLEAN,
    reason TEXT
);

SELECT create_hypertable('llm_telemetry', 'timestamp', if_not_exists => TRUE);
