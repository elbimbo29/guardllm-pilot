-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. LLM Requests Telemetry Table
CREATE TABLE IF NOT EXISTS llm_requests (
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(64) NOT NULL,
    model VARCHAR(64) NOT NULL,
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status_code INT NOT NULL DEFAULT 200
);

-- Convert llm_requests into a TimescaleDB hypertable partitioned by time
SELECT create_hypertable('llm_requests', 'time', if_not_exists => TRUE);

-- Index for quick request_id lookups
CREATE INDEX IF NOT EXISTS idx_llm_requests_request_id ON llm_requests (request_id, time DESC);


-- 2. Guardrail Evaluations Telemetry Table
CREATE TABLE IF NOT EXISTS guardrail_evaluations (
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(64) NOT NULL,
    passed BOOLEAN NOT NULL,
    overall_action VARCHAR(16) NOT NULL,
    execution_time_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    rule_results JSONB NOT NULL DEFAULT '[]'::jsonb
);

-- Convert guardrail_evaluations into a TimescaleDB hypertable partitioned by time
SELECT create_hypertable('guardrail_evaluations', 'time', if_not_exists => TRUE);

-- Index for filtering by action and time
CREATE INDEX IF NOT EXISTS idx_guardrail_evals_action ON guardrail_evaluations (overall_action, time DESC);
CREATE INDEX IF NOT EXISTS idx_guardrail_evals_request_id ON guardrail_evaluations (request_id, time DESC);
