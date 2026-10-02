"""Week 5 execution trace runner for the UtiliCare bounded agent.

Produces the remaining execution traces needed for the "Three execution
traces" deliverable. evidence/traces/week5_bounded_agent_trace.json
(already in the repo) counts as trace 1 -- a baseline success case
(outage report -> tool calls -> ticket drafted, 1 iteration). This script
produces traces 2 and 3 by running the REAL src.bounded_agent.run_bounded_agent()
against the live Gemini API (no mocking) and logging the full step-by-step
state for each run.

Trace 2: an ambiguous message, to see how the real pipeline handles a
         less clear-cut case than trace 1 (different stop_reason expected).
Trace 3: the required failure/recovery case. GEMINI_API_KEY is swapped
         for an invalid value for this run ONLY, forcing a genuine
         authentication failure from the live API. This proves
         run_bounded_agent()'s except-Exception handling (Agent Task
         Contract 5.2, "Tool execution failure" / API failure path)
         classifies the failure and stops safely with a recorded
         stop_reason, instead of crashing the process. The real
         GEMINI_API_KEY is restored immediately afterward, whatever
         happens.

Run with:
    python -m tests.run_week5_execution_traces
"""

from __future__ import annotations

import json
import os
import time

from src.bounded_agent import run_bounded_agent

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "evidence", "traces")

RUNS = [
    {
        "trace_id": "run2_ambiguous_message",
        "message": "something is wrong with my service, not sure what exactly",
        "note": (
            "Deliberately vague message with no clear category signal, to "
            "exercise a different path than trace 1's clean outage report -- "
            "expected to land on 'other'/low confidence and possibly "
            "clarification_needed, but the real model's actual behaviour is "
            "what gets recorded here, not an assumption."
        ),
        "force_api_failure": False,
    },
]

# Note: a forced-failure (invalid API key) run is no longer needed here --
# a genuine, naturally-occurring model_parsing_failure (MAX_TOKENS truncation)
# was already captured and saved as
# evidence/traces/week5_execution_trace_run3_model_parsing_failure.json,
# which serves as trace 3.


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    original_key = os.environ.get("GEMINI_API_KEY")

    for run in RUNS:
        print("=" * 70)
        print(f"{run['trace_id']}")
        print(f"Message: {run['message']}")
        print(f"Note: {run['note']}")
        print("=" * 70)

        if run["force_api_failure"]:
            os.environ["GEMINI_API_KEY"] = "INVALID-KEY-FOR-WEEK5-FAILURE-TEST"

        try:
            final_state = run_bounded_agent(run["message"])
        finally:
            # Restore the real key immediately, whether this run succeeded,
            # failed cleanly, or raised something unexpected.
            if original_key is not None:
                os.environ["GEMINI_API_KEY"] = original_key
            elif "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

        out_path = os.path.join(
            RESULTS_DIR, f"week5_execution_trace_{run['trace_id']}.json"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "trace_id": run["trace_id"],
                    "input_message": run["message"],
                    "note": run["note"],
                    "final_state": final_state,
                },
                f,
                indent=2,
                default=str,
            )

        print(f"stop_reason: {final_state.get('stop_reason')}")
        print(f"iteration_count: {final_state.get('iteration_count')}")
        print(f"Wrote {out_path}\n")

        time.sleep(3)  # be gentle with free-tier rate limits between runs


if __name__ == "__main__":
    main()
