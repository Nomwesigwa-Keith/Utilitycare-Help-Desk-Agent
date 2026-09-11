"""
main.py — exposes the triage agent as a local HTTP endpoint.

Run with:
    uvicorn src.main:app --reload

Then test with:
    curl -X POST http://127.0.0.1:8000/triage \
        -H "Content-Type: application/json" \
        -d '{"message": "My bill seems way too high this month"}'
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agent import call_agent

app = FastAPI(title="UtiliCare Help-Desk Triage Agent")


class TriageRequest(BaseModel):
    message: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/triage")
def triage(req: TriageRequest) -> dict:
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        result = call_agent(req.message)
    except RuntimeError as e:
        # e.g. missing API key
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model call failed: {e}")

    return result
