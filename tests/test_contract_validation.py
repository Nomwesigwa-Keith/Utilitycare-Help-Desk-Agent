"""Regression tests for model and tool output contracts."""

from __future__ import annotations

import json

import pytest

from src.agent import _parse_model_json
from src.orchestrator import ToolExecutionError, execute_tool_call
from src.tools import TOOL_REGISTRY


def _model_response(**overrides: object) -> str:
    response = {
        "category": "billing",
        "confidence": "high",
        "summary": "The customer is asking about a billing charge.",
        "grounded_guidance": "Review the controlled billing guidance.",
        "grounding_status": "grounded",
        "requires_clarification": False,
        "clarifying_question": None,
    }
    response.update(overrides)
    return json.dumps(response)


def test_model_parser_rejects_summary_over_25_words():
    raw = _model_response(summary=" ".join(["word"] * 26))

    parsed, error = _parse_model_json(raw)

    assert parsed is None
    assert error == "response summary must contain at most 25 words"


def test_model_parser_rejects_invalid_tool_call_name():
    raw = _model_response(
        tool_calls=[{"name": "", "arguments": {}}],
    )

    parsed, error = _parse_model_json(raw)

    assert parsed is None
    assert error == "tool_call name must be a non-empty string"


@pytest.mark.parametrize(
    ("tool_name", "arguments", "extra_field"),
    [
        (
            "get_outage_status",
            {"area_code": "NDA", "service_type": "electricity"},
            "unexpected",
        ),
        (
            "draft_ticket",
            {
                "category": "billing_query",
                "priority": "medium",
                "summary": "Duplicate charge",
                "customer_area_code": "KLA",
            },
            "unexpected",
        ),
    ],
)
def test_tool_results_reject_unexpected_fields(
    tool_name: str, arguments: dict[str, str], extra_field: str
):
    original = TOOL_REGISTRY[tool_name]["function"]

    def malformed_result(**_kwargs: object) -> dict[str, object]:
        if tool_name == "get_outage_status":
            return {
                "outage_active": False,
                "estimated_restoration": None,
                "affected_area_description": "No outage",
                extra_field: True,
            }
        return {
            "draft_id": "DRAFT-TEST",
            "status": "pending_approval",
            "draft_summary": "Draft",
            extra_field: True,
        }

    TOOL_REGISTRY[tool_name]["function"] = malformed_result
    try:
        with pytest.raises(ToolExecutionError, match="unexpected fields"):
            execute_tool_call(tool_name, arguments)
    finally:
        TOOL_REGISTRY[tool_name]["function"] = original
