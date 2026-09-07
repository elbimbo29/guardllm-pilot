import os
from pathlib import Path


# Define project root
BASE_DIR = (
    Path(__file__).resolve().parent.parent if "scripts" in os.getcwd() else Path.cwd()
)

# List of all directories to create
DIRECTORIES = [
    ".github/workflows",
    "cicd",
    "docs",
    "deploy",
    "fastapi",
    "deepeval",
    "otel",
    "streamlit",
    "dashboard/grafana",
    "scripts",
    "tests",
    "dataset",
]

# Files with initial starter content
FILES = {
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
env/
venv/

# Environment variables
.env

# IDEs
.vscode/
.idea/

# Testing & Logs
.pytest_cache/
*.log
""",
    ".env.example": """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# OpenTelemetry / Jaeger Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# TimescaleDB Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=guardllm_db
DB_USER=admin
DB_PASSWORD=adminpass
""",
    "requirements.txt": """fastapi==0.110.0
uvicorn==0.28.0
streamlit==1.32.0
openai==1.14.0
deepeval==0.20.0
opentelemetry-api==1.23.0
opentelemetry-sdk==1.23.0
opentelemetry-exporter-otlp-proto-grpc==1.23.0
opentelemetry-instrumentation-fastapi==0.44b0
psycopg2-binary==2.9.9
requests==2.31.0
python-dotenv==1.0.1
pytest==8.0.2
""",
    "README.md": """# GuardLLM Pilot 🛡️
> Operational LLM Observability, Real-Time Evaluation & Guardrail Proxy

## System Architecture Overview
GuardLLM Pilot is a production-grade LLM proxy engineered to evaluate model outputs in real time using **DeepEval**, record multi-step latency spans using **OpenTelemetry & Jaeger**, log persistent performance metrics in **TimescaleDB**, and present live telemetry in **Grafana** and **Streamlit**.

## Quickstart Guide
1. Launch containerized services: `docker-compose -f cicd/docker-compose.yml up -d`
2. Run FastAPI Proxy: `uvicorn fastapi.main:app --reload`
3. Launch Streamlit UI: `streamlit run streamlit/app.py`
""",
    "fastapi/__init__.py": "",
    "fastapi/main.py": """# GuardLLM FastAPI Proxy Orchestrator Entrypoint
from fastapi import FastAPI

app = FastAPI(title="GuardLLM Pilot Proxy")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "GuardLLM Proxy"}
""",
    "fastapi/schemas.py": "# Pydantic models for request/response validation\n",
    "fastapi/db.py": "# TimescaleDB async connection pool and query execution\n",
    "deepeval/__init__.py": "",
    "deepeval/metrics.py": "# DeepEval metric configuration (Hallucination, Faithfulness)\n",
    "deepeval/evaluator.py": "# LLM-as-a-Judge inspection and threshold enforcement logic\n",
    "otel/__init__.py": "",
    "otel/tracer.py": "# OpenTelemetry TracerProvider and OTLP gRPC Exporter setup\n",
    "otel/spans.py": "# Custom span context managers for LLM calls and evaluation steps\n",
    "streamlit/app.py": "# Streamlit Interactive Dashboard Entrypoint\nimport streamlit as st\n\nst.title('🛡️ GuardLLM Pilot Dashboard')\n",
    "streamlit/components.py": "# Custom Streamlit components (Status badges, Metric cards)\n",
    "cicd/init_db.sql": """-- TimescaleDB Initialization Schema
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
""",
    "cicd/docker-compose.yml": """version: '3.8'

services:
  jaeger:
    image: cr.jaegertracing.io/jaegertracing/jaeger:2.20.0
    container_name: jaeger_guardllm
    ports:
      - "16686:16686" # UI
      - "4317:4317"   # OTLP gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  timescaledb:
    image: timescale/timescaledb:latest-pg16
    container_name: timescaledb_guardllm
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=guardllm_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=adminpass
    volumes:
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql

  grafana:
    image: grafana/grafana:latest
    container_name: grafana_guardllm
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - jaeger
      - timescaledb
""",
    "cicd/docker-compose.prod.yml": "# Production Docker Compose file\n",
    "docs/ARCHITECTURE.md": "# System Execution Flow & Architecture Documentation\n",
    "docs/API_SPEC.md": "# FastAPI OpenAPI / Swagger Endpoint Documentation\n",
    "docs/DASHBOARDS.md": "# Grafana & Jaeger Visual Dashboard Configuration Guide\n",
    "deploy/Dockerfile.fastapi": "# Production Dockerfile for FastAPI Backend\n",
    "deploy/Dockerfile.streamlit": "# Production Dockerfile for Streamlit UI\n",
    "deploy/render_deploy.sh": "#!/bin/bash\n# Cloud deployment commands\n",
    "dashboard/grafana/datasources.yaml": "# Grafana Datasources Provisioning (TimescaleDB & Jaeger)\n",
    "dashboard/grafana/guardllm_dashboard.json": '{\n  "dashboard": "GuardLLM Observability"\n}\n',
    "scripts/run_local.sh": "#!/bin/bash\n# Local environment initialization\n",
    "tests/conftest.py": "# PyTest fixtures and mock LLM response objects\n",
    "tests/test_fastapi.py": "# FastAPI endpoint integration unit tests\n",
    "tests/test_eval_benchmarks.py": "# DeepEval benchmark dataset regression tests\n",
    "dataset/benchmark_cases.json": '[\n  {\n    "prompt": "What is the return window?",\n    "context": "Returns are allowed within 30 days.",\n    "expected_output": "30 days"\n  }\n]\n',
    ".github/workflows/eval_ci.yml": """name: GuardLLM CI/CD Quality Gate

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test_and_eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run Unit & Benchmark Tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pytest tests/
""",
}


def create_structure():
    print("🚀 Initializing GuardLLM Pilot directory structure...")

    # 1. Create Directories
    for folder in DIRECTORIES:
        dir_path = BASE_DIR / folder
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  [DIR]  Created: {folder}/")

    # 2. Create Files
    for relative_path, content in FILES.items():
        file_path = BASE_DIR / relative_path
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [FILE] Created: {relative_path}")
        else:
            print(f"  [SKIP] Exists:  {relative_path}")

    print(
        "\n✅ Setup complete! Project tree and boilerplate files initialized successfully."
    )


if __name__ == "__main__":
    create_structure()
