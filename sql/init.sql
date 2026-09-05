-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. Table for API Proxy Request Logs
CREATE TABLE IF NOT EXISTS llm_requests (
    time TIMESTAMPTZ NOT NULL,
    request_id UUID NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    status_code INT NOT NULL,
    guardrail_status VARCHAR(50) DEFAULT 'PASSED',
    prompt_text TEXT,
    response_text TEXT
);

-- Convert to TimescaleDB Hypertable partitioned by time
SELECT create_hypertable('llm_requests', 'time', if_not_exists => TRUE);

-- 2. Table for Guardrail & Evaluation Metrics
CREATE TABLE IF NOT EXISTS guardrail_evaluations (
    time TIMESTAMPTZ NOT NULL,
    request_id UUID NOT NULL,
    evaluator_name VARCHAR(100) NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    reason TEXT
);

-- Convert guardrail_evaluations to Hypertable
SELECT create_hypertable('guardrail_evaluations', 'time', if_not_exists => TRUE);

-- Create indexes for performance on high-volume queries
CREATE INDEX IF NOT EXISTS idx_requests_model ON llm_requests (model, time DESC);
CREATE INDEX IF NOT EXISTS idx_evals_request_id ON guardrail_evaluations (request_id, time DESC);