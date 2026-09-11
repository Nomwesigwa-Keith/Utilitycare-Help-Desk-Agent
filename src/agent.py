"""
agent.py — Baseline model integration for the UtiliCare Help-Desk Triage Agent.

This module owns the one job of "talking to Gemini": given a raw customer
message, send it to the model and return a structured (JSON-able) result.

Prompt behavior (role, rules, output format) will live in
prompts/prompt_spec.md once that's ready (Khot Adet's task) — for now this
uses a minimal placeholder system prompt just to prove the wiring works and
returns real JSON, not an error.
"""

import os
import json
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Model ID for Gemini
MODEL_ID = os.environ.get("UTILICARE_MODEL", "models/gemini-flash-latest")

# Placeholder — replace with the real spec once prompts/prompt_spec.md exists.
PLACEHOLDER_SYSTEM_PROMPT = (
    "You are a help-desk triage assistant for UtiliCare, a utility company. "
    "Classify the customer's message into one category and reply with ONLY "
    "a JSON object, no other text, in this exact shape: "
    '{"category": "<string>", "confidence": "<low|medium|high>", '
    '"summary": "<one sentence>"}. '
    "Valid categories: billing, outage, service_request, account, complaint, "
    "other."
)


def _get_client() -> genai.GenerativeModel:
    """Configure the Gemini client. Reads GEMINI_API_KEY from env."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Create a .env file (see "
            ".env.example) or export it in your shell before running."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_ID, system_instruction=PLACEHOLDER_SYSTEM_PROMPT)


def call_agent(message: str) -> dict[str, Any]:
    """
    Send a single customer message to Gemini and return a parsed dict.

    Returns a dict with at least:
      - "raw_text": the exact text Gemini returned
      - "parsed": the JSON-decoded object if parsing succeeded, else None
      - "parse_error": error string if JSON parsing failed, else None
    """
    model = _get_client()

    response = model.generate_content(
        message,
        generation_config=genai.GenerationConfig(
            max_output_tokens=300,
            temperature=0.7,
        )
    )

    raw_text = response.text.strip()

    parsed = None
    parse_error = None
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        parse_error = str(e)

    return {
        "raw_text": raw_text,
        "parsed": parsed,
        "parse_error": parse_error,
        "model": MODEL_ID,
        "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
        "usage": {
            "input_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
            "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 0,
        },
    }


if __name__ == "__main__":
    # Quick manual smoke test:
    #   python -m src.agent
    # Confirms you get a real response back, not an error.
    test_message = "My power has been out since this morning, when will it be back?"
    result = call_agent(test_message)
    print(json.dumps(result, indent=2))
