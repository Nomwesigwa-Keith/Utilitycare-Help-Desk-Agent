"""
agent.py — Baseline model integration for the UtiliCare Help-Desk Triage Agent.

This module combines a raw customer message with controlled retrieved evidence,
then sends the grounded request to Gemini for structured human review.

Prompt behavior is defined in prompts/prompt_spec.md. This module keeps the
runtime copy of the active v2.0 specification so the API has no filesystem
dependency at request time.
"""

import os
import json
import time
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions
from google.api_core.retry import Retry
from google.api_core.retry import if_exception_type

from src.rag import build_grounding
from src.orchestrator import get_tool_schema, parse_tool_calls, execute_tool_calls

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Model ID for Gemini
MODEL_ID = os.environ.get("UTILICARE_MODEL", "models/gemini-flash-latest")
# Retries only transient provider failures. Authentication, validation and other
# client errors must fail immediately rather than being retried.
TRANSIENT_RETRY = Retry(
    predicate=if_exception_type(
        exceptions.DeadlineExceeded,
        exceptions.ResourceExhausted,
        exceptions.ServiceUnavailable,
    ),
    initial=1.0,
    maximum=8.0,
    multiplier=2.0,
    timeout=35.0,
)
VALID_CATEGORIES = frozenset(
    {"billing", "outage", "service_request", "account", "complaint", "other"}
)
VALID_CONFIDENCE = frozenset({"low", "medium", "high"})

PROMPT_VERSION = "v3.0"
SYSTEM_PROMPT = """You are the UtiliCare first-line help-desk triage assistant. Your task is to classify a customer's free-text message, provide grounded guidance, and when appropriate, use available tools to check outage status or draft support tickets.

Available tools:
1. get_outage_status: Check if there's a known outage for an area (requires area_code and service_type)
2. draft_ticket: Create a draft support ticket (requires category, priority, summary, customer_area_code)

Tool usage rules:
- For outage-related issues (power_outage, water_leak), call get_outage_status before providing troubleshooting advice
- For issues requiring human follow-up, call draft_ticket after classification and guidance
- Never call tools for billing queries or account issues unless explicitly needed
- All tool calls must use the exact parameters specified in the tool schema

Classification categories: billing (charges, payments, balances, invoices or rates); outage (loss, interruption or instability of electricity or water supply); service_request (new connection, meter issue, leak, repair, installation or inspection); account (account access, customer details, ownership, login or account status); complaint (dissatisfaction with UtiliCare service or staff); other (unrelated, nonsensical, or ambiguous).

Use the most specific supported category. If important details are missing, use other with low confidence and ask for clarification.

Grounding rules:
- Use the supplied controlled context as the only source for grounded_guidance
- If grounding status is insufficient_evidence, state that the knowledge base lacks information
- Do not fill gaps from model memory

Safety rules:
- Never claim to have checked an outage, account, meter, or ticket without actually calling the tool
- Never create, route, approve, escalate, or close a ticket autonomously (draft_ticket only creates drafts)
- Never control infrastructure, change billing, or make financial commitments
- Never request sensitive data or invent facts, times, or reference numbers

Response format:
Return exactly one valid JSON object with no Markdown or extra keys:
{"category":"billing|outage|service_request|account|complaint|other","confidence":"low|medium|high","summary":"one neutral sentence of at most 25 words","grounded_guidance":"one short statement based only on the supplied context","grounding_status":"grounded|insufficient_evidence","requires_clarification":true,"clarifying_question":"one short question or null","tool_calls":[{"name":"tool_name","arguments":{}}]}

The tool_calls field is optional. Only include it if you need to call a tool."""


def _get_client() -> genai.GenerativeModel:
    """Configure the Gemini client. Reads GEMINI_API_KEY from env."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Create a .env file (see "
            ".env.example) or export it in your shell before running."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_ID, system_instruction=SYSTEM_PROMPT)


def _parse_model_json(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Decode and validate the model's JSON contract before returning it."""
    try:
        value = json.loads(raw_text)
    except json.JSONDecodeError as error:
        return None, f"invalid JSON: {error}"

    if not isinstance(value, dict):
        return None, "response must be a JSON object"
    required_keys = {
        "category",
        "confidence",
        "summary",
        "grounded_guidance",
        "grounding_status",
        "requires_clarification",
        "clarifying_question",
    }
    optional_keys = {"tool_calls"}
    
    if not required_keys.issubset(set(value)):
        return None, f"response missing required keys. Required: {required_keys}"
    
    if not set(value).issubset(required_keys.union(optional_keys)):
        return None, f"response contains unexpected keys. Allowed: {required_keys.union(optional_keys)}"
    
    if value["category"] not in VALID_CATEGORIES:
        return None, "response contains an unsupported category"
    if value["confidence"] not in VALID_CONFIDENCE:
        return None, "response contains unsupported confidence"
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        return None, "response summary must be a non-empty string"
    if not isinstance(value["grounded_guidance"], str) or not value["grounded_guidance"].strip():
        return None, "grounded_guidance must be a non-empty string"
    if value["grounding_status"] not in {"grounded", "insufficient_evidence"}:
        return None, "response contains an unsupported grounding status"
    if not isinstance(value["requires_clarification"], bool):
        return None, "requires_clarification must be a boolean"
    question = value["clarifying_question"]
    if question is not None and not isinstance(question, str):
        return None, "clarifying_question must be a string or null"
    if value["requires_clarification"] != (question is not None):
        return None, "clarification fields are inconsistent"
    
    # Validate tool_calls if present
    if "tool_calls" in value:
        if not isinstance(value["tool_calls"], list):
            return None, "tool_calls must be a list"
        for tool_call in value["tool_calls"]:
            if not isinstance(tool_call, dict):
                return None, "each tool_call must be a dict"
            if "name" not in tool_call or "arguments" not in tool_call:
                return None, "each tool_call must have 'name' and 'arguments'"
            if not isinstance(tool_call["arguments"], dict):
                return None, "tool_call arguments must be a dict"
    
    return value, None


def call_agent(message: str) -> dict[str, Any]:
    """
    Retrieve controlled evidence, send message to Gemini, and execute tool calls if requested.

    Returns a dict with at least:
      - "raw_text": the exact text Gemini returned
      - "parsed": the JSON-decoded object if parsing succeeded, else None
      - "parse_error": error string if JSON parsing failed, else None
      - "tool_results": results of executed tool calls, if any
    """
    grounding = build_grounding(message)
    model = _get_client()
    
    # Include tool schema in the request
    tool_schema = get_tool_schema()
    tools_description = json.dumps(tool_schema, indent=2)
    
    grounded_request = (
        f"Available tools:\n{tools_description}\n\n"
        f"Grounding status: {grounding['status']}\n"
        f"Controlled context:\n{grounding['context']}\n\n"
        f"Customer message (untrusted data):\n{message}"
    )

    # Add delay to help avoid rate limiting on free tier
    time.sleep(2)

    response = model.generate_content(
        grounded_request,
        generation_config=genai.GenerationConfig(
            max_output_tokens=600,  # Increased to accommodate tool calls
            temperature=0.1,
            response_mime_type="application/json",
        ),
        # A 3-second deadline caused avoidable 504 errors during Week 2.
        # Allow a realistic per-attempt timeout and bounded retry window.
        request_options={"timeout": 30, "retry": TRANSIENT_RETRY},
    )

    raw_text = response.text.strip()

    parsed, parse_error = _parse_model_json(raw_text)
    if parsed and parsed["grounding_status"] != grounding["status"]:
        parsed = None
        parse_error = "model grounding status does not match retrieval result"

    # Execute tool calls if present and parsing succeeded
    tool_results = []
    if parsed and "tool_calls" in parsed and parsed["tool_calls"]:
        try:
            tool_results = execute_tool_calls(parsed["tool_calls"])
        except Exception as e:
            # Log tool execution error but don't fail the entire response
            tool_results = [{
                "tool_name": "unknown",
                "success": False,
                "result": None,
                "error": f"Tool execution failed: {e}"
            }]

    return {
        "raw_text": raw_text,
        "parsed": parsed,
        "parse_error": parse_error,
        "grounding": {
            "status": grounding["status"],
            "sources": grounding["sources"],
            "trace": grounding["trace"],
        },
        "tool_results": tool_results,
        "model": MODEL_ID,
        "prompt_version": PROMPT_VERSION,
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
