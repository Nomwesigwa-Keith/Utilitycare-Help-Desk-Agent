"""
Week 5 bounded agent workflow for the UtilityCare Triage Agent.

Implements Sense -> Plan -> Act -> Observe -> Stop/Re-plan,
per docs/requirements/Agent_Task_Contract_for_week_5.docx
"""
from src.agent import call_agent

MAX_ITERATIONS = 3


def create_initial_state(customer_message: str) -> dict:
    """
    Builds the starting state for one bounded-agent run,
    per Agent Task Contract section 3.1.
    """
    return {
        "customer_message": customer_message,
        "classification_result": None,
        "grounding_status": None,
        "retrieved_sources": [],
        "tool_calls_made": [],
        "tool_results": [],
        "iteration_count": 0,
        "requires_clarification": False,
        "clarifying_question": None,
        "stop_reason": None,
    }


def check_stop_condition(state: dict, latest_result: dict) -> str | None:
    """
    Checks state + the latest call_agent() result against the Agent Task
    Contract's stop conditions (section 5). Returns a stop_reason string
    if the loop should stop, or None if it should continue/re-plan.
    """
    parsed = latest_result.get("parsed")

    # 5.2 Failure: couldn't even parse a response
    if parsed is None:
        return "model_parsing_failure"

    # 5.2 Failure: iteration limit reached
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "iteration_limit_reached"

    # 5.1 Success: clarification needed
    if parsed.get("requires_clarification"):
        return "clarification_needed"

    # 5.4 Hand-off: a ticket draft was created this step
    tool_results = latest_result.get("tool_results", [])
    for result in tool_results:
        if result.get("tool_name") == "draft_ticket" and result.get("success"):
            return "ticket_drafted_pending_approval"

    # 5.2 Failure: any tool call failed and can't be recovered
    for result in tool_results:
        if not result.get("success"):
            return "tool_execution_failure"

    # 5.1 Success: grounded guidance given, no outstanding tool need
    if parsed.get("grounding_status") == "grounded" and not tool_results:
        return "goal_achieved_grounded_guidance"

    # Nothing matched -> no stop condition met, loop may continue
    return None


def run_bounded_agent(customer_message: str) -> dict:
    """
    Runs the bounded Sense->Plan->Act->Observe->Stop/Re-plan workflow
    described in the Week 5 Agent Task Contract.

    Returns the final state dict, including a full trace of every
    iteration for evidence/logging purposes.
    """
    state = create_initial_state(customer_message)
    trace = []

    while state["iteration_count"] < MAX_ITERATIONS:
        state["iteration_count"] += 1

        # --- Sense + Plan + Act happen inside call_agent() already ---
        # (it retrieves grounding, classifies, and may call tools in one pass)
        try:
            result = call_agent(customer_message)
        except Exception as e:
            # The API call itself failed (timeout, network error, etc.)
            # Treat this as a recoverable failure: record it and stop safely
            # rather than letting the whole program crash.
            error_text = str(e)
            stop_reason = (
                "quota_exhausted"
                if "429" in error_text or "quota exceeded" in error_text.lower()
                else "provider_unavailable"
                if "503" in error_text or "high demand" in error_text.lower()
                else "api_call_failed"
            )
            trace.append({
                "iteration": state["iteration_count"],
                "raw_text": None,
                "parsed": None,
                "tool_results": [],
                "error": error_text,
            })
            state["stop_reason"] = stop_reason
            state["trace"] = trace
            return state

        # --- Observe: update our state with what happened this step ---
        parsed = result.get("parsed")
        if parsed:
            state["classification_result"] = {
                "category": parsed.get("category"),
                "confidence": parsed.get("confidence"),
            }
            state["grounding_status"] = parsed.get("grounding_status")
            state["requires_clarification"] = parsed.get("requires_clarification", False)
            state["clarifying_question"] = parsed.get("clarifying_question")

        state["retrieved_sources"] = result.get("grounding", {}).get("sources", [])
        tool_results = result.get("tool_results", [])
        state["tool_results"].extend(tool_results)
        state["tool_calls_made"].extend(
            [{"tool_name": r.get("tool_name")} for r in tool_results]
        )

        # Record this step in the trace, for the evidence deliverable
        trace.append({
            "iteration": state["iteration_count"],
            "raw_text": result.get("raw_text"),
            "parsed": parsed,
            "parse_error": result.get("parse_error"),
            "finish_reason": result.get("finish_reason"),
            "tool_results": tool_results,
        })

        # --- Stop/Re-plan decision ---
        stop_reason = check_stop_condition(state, result)
        if stop_reason:
            state["stop_reason"] = stop_reason
            break
        # else: no stop condition met -> loop continues (re-plan)

    else:
        # while-loop exhausted MAX_ITERATIONS without an explicit stop match
        state["stop_reason"] = "iteration_limit_reached"

    state["trace"] = trace
    return state


if __name__ == "__main__":
    # Quick manual smoke test:
    #   python -m src.bounded_agent
    import json

    test_message = "My power has been out since last night in Ntinda."
    final_state = run_bounded_agent(test_message)
    print(json.dumps(final_state, indent=2, default=str))