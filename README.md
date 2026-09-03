# GuardLLM Pilot 🛡️
> Operational LLM Observability, Real-Time Evaluation & Guardrail Proxy

## System Architecture Overview
GuardLLM Pilot is a production-grade LLM proxy engineered to evaluate model outputs in real time using **DeepEval**, record multi-step latency spans using **OpenTelemetry & Jaeger**, log persistent performance metrics in **TimescaleDB**, and present live telemetry in **Grafana** and **Streamlit**.

## Quickstart Guide
1. Launch containerized services: `docker-compose -f cicd/docker-compose.yml up -d`
2. Run FastAPI Proxy: `uvicorn fastapi.main:app --reload`
3. Launch Streamlit UI: `streamlit run streamlit/app.py`
