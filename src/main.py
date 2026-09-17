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
from google.api_core import exceptions
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
    except exceptions.RetryError as error:
        # The retry wrapper retains the actual final provider error as `cause`.
        cause = error.cause
        if isinstance(cause, exceptions.ResourceExhausted):
            raise HTTPException(
                status_code=429,
                detail="Gemini quota or request-rate limit remained exhausted after retries.",
            )
        if isinstance(cause, exceptions.DeadlineExceeded):
            raise HTTPException(
                status_code=504,
                detail="Gemini did not respond before the retry deadline.",
            )
        raise HTTPException(
            status_code=503,
            detail="Gemini remained temporarily unavailable after retries.",
        )
    except exceptions.ResourceExhausted:
        raise HTTPException(
            status_code=429,
            detail="Gemini quota or request-rate limit reached. Wait and retry.",
        )
    except exceptions.ServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Gemini is temporarily unavailable. Retry after a short delay.",
        )
    except exceptions.DeadlineExceeded:
        raise HTTPException(
            status_code=504,
            detail="Gemini did not respond before the client deadline. Retry the request.",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model call failed: {e}")

    return result
