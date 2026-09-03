# GuardLLM FastAPI Proxy Orchestrator Entrypoint
from fastapi import FastAPI

app = FastAPI(title="GuardLLM Pilot Proxy")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "GuardLLM Proxy"}
