# GuardLLM Pilot 🛡️
> Operational LLM Observability, Real-Time Evaluation & Guardrail Proxy

## System Architecture Overview
GuardLLM Pilot is a production-grade LLM proxy engineered to evaluate model outputs in real time using **DeepEval**, record multi-step latency spans using **OpenTelemetry & Jaeger**, log persistent performance metrics in **TimescaleDB**, and present live telemetry in **Grafana** and **Streamlit**.

## Quickstart Guide
1. Launch containerized services: `docker-compose -f cicd/docker-compose.yml up -d`
2. Run FastAPI Proxy: `uvicorn fastapi.main:app --reload`
3. Launch Streamlit UI: `streamlit run streamlit/app.py`

## Full System Deployment Guide
## 1. Clone repository and start all 5 services
git clone <your-repo-url>
cd guardllm-pilot
docker compose up -d --build

## 2. Endpoints:
# - GuardLLM Proxy API:       http://localhost:8000
# - Grafana Telemetry:         http://localhost:3000 (admin/admin)
# - Streamlit Audit Portal:    http://localhost:8501
# - Locust Load Testing UI:    http://localhost:8089

flowchart TD
    %% Styling Definitions
    classDef client fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef proxy fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;
    classDef storage fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
    classDef observability fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
    classDef testing fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f;

    %% Client Layer
    SubGraphClient["Client / Applications"]
    Client["REST Client / OpenAI SDK<br><i>v1/chat/completions</i>"]:::client
    SubGraphClient --- Client

    %% Proxy Layer
    subgraph GuardLLMProxy ["GuardLLM Proxy Service (FastAPI - Port 8000)"]
        direction TB
        Ingress["<b>Ingress Middleware</b><br>• Request ID Injector (X-Request-ID)<br>• CORS & Rate Limiter"]
        
        subgraph Pipeline ["Guardrail Rule Execution Engine"]
            direction TB
            Rule1{"1. Prompt Injection Guard"}
            Rule2{"2. PII Detection & Sanitization"}
            Rule3{"3. Toxicity Guard"}
        end

        Upstream["<b>Upstream Adapter</b><br>Forwards sanitized payload to<br>Upstream LLM (OpenAI API)"]
        AsyncWriter["<b>Async Telemetry Writer</b><br>Non-blocking background worker<br>(asyncpg connection pool)"]
    end
    class GuardLLMProxy proxy

    %% Storage Layer
    subgraph Storage ["Database Layer"]
        TimescaleDB[("<b>TimescaleDB</b> (Port 5432)<br>Hypertable: <i>guardrail_evaluations</i><br>• Request ID, Latency, Action<br>• Deep Rules Applied (JSONB)")]:::storage
    end

    %% Observability Layer
    subgraph Observability ["Monitoring & Audit Stack"]
        Grafana["<b>Grafana</b> (Port 3000)<br>• Throughput (RPS)<br>• Action Split (PASS/MASK/BLOCK)<br>• Latency Percentiles (p50, p95, p99)"]:::observability
        Streamlit["<b>Streamlit Portal</b> (Port 8501)<br>• Deep JSONB Audit Inspector<br>• Log Search & Compliance Filters"]:::observability
    end

    %% Testing Layer
    subgraph LoadTesting ["Benchmarking Suite"]
        Locust["<b>Locust Engine</b> (Port 8089)<br>Multi-route traffic model:<br>60% PASS | 30% MASK | 10% BLOCK"]:::testing
    end

    %% Flow Relationships
    Client -->|"HTTP POST (Port 8000)"| Ingress
    Ingress --> Rule1
    
    Rule1 -->|"BLOCK (Injection Detected)"| ErrResponse["Return HTTP 400/403 Error"]
    Rule1 -->|"PASS"| Rule2
    
    Rule2 -->|"Match (PII Found)"| MaskData["Mask Payload<br>[EMAIL], [PHONE]"]
    Rule2 -->|"PASS"| Rule3
    MaskData --> Rule3
    
    Rule3 -->|"BLOCK (Toxicity High)"| ErrResponse
    Rule3 -->|"PASS / MASK"| Upstream

    Upstream -->|"HTTP 200 OK Response"| Client
    
    ErrResponse -.->|"Log Event"| AsyncWriter
    Upstream -.->|"Log Metadata"| AsyncWriter

    AsyncWriter -->|"Async Batch Write"| TimescaleDB

    TimescaleDB -->|"SQL Telemetry Queries"| Grafana
    TimescaleDB -->|"SQL Audit Queries"| Streamlit

    Locust -->|"Simulated Load Traffic"| Ingress