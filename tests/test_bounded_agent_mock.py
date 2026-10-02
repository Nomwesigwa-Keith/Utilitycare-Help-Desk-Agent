"""
Offline test for the bounded agent loop, using a fake call_agent()
so we can verify the Sense->Plan->Act->Observe->Stop logic without
spending real API quota. This does NOT replace real execution traces
with the live model -- it just proves the loop behaves correctly.
"""
from unittest.mock import patch
from src import bounded_agent


def test_stops_on_grounded_guidance_no_tools():
    fake_result = {
        "raw_text": "...",
        "parsed": {
            "category": "outage",
            "confidence": "high",
            "grounding_status": "grounded",
            "requires_clarification": False,
            "clarifying_question": None,
        },
        "grounding": {"sources": []},
        "tool_results": [],
    }
    with patch("src.bounded_agent.call_agent", return_value=fake_result):
        state = bounded_agent.run_bounded_agent("test message")
    assert state["stop_reason"] == "goal_achieved_grounded_guidance"
    assert state["iteration_count"] == 1
    print("PASS: stops correctly on grounded guidance, no tools needed")


def test_stops_on_ticket_drafted():
    fake_result = {
        "raw_text": "...",
        "parsed": {
            "category": "outage",
            "confidence": "high",
            "grounding_status": "grounded",
            "requires_clarification": False,
            "clarifying_question": None,
        },
        "grounding": {"sources": []},
        "tool_results": [
            {"tool_name": "draft_ticket", "success": True, "result": {"draft_id": "DRAFT-1"}}
        ],
    }
    with patch("src.bounded_agent.call_agent", return_value=fake_result):
        state = bounded_agent.run_bounded_agent("test message")
    assert state["stop_reason"] == "ticket_drafted_pending_approval"
    print("PASS: stops correctly after ticket drafted, awaiting approval")


def test_stops_on_iteration_limit():
    fake_result = {
        "raw_text": "...",
        "parsed": {
            "category": "other",
            "confidence": "low",
            "grounding_status": "insufficient_evidence",
            "requires_clarification": False,
            "clarifying_question": None,
        },
        "grounding": {"sources": []},
        "tool_results": [],
    }
    with patch("src.bounded_agent.call_agent", return_value=fake_result):
        state = bounded_agent.run_bounded_agent("test message")
    assert state["iteration_count"] == bounded_agent.MAX_ITERATIONS
    assert state["stop_reason"] == "iteration_limit_reached"
    print("PASS: correctly stops at MAX_ITERATIONS instead of looping forever")


if __name__ == "__main__":
    test_stops_on_grounded_guidance_no_tools()
    test_stops_on_ticket_drafted()
    test_stops_on_iteration_limit()
    print("\nAll mock tests passed.")