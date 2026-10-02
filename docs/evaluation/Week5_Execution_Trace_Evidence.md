# Week 5 Execution Trace Evidence

## Purpose

This note records three real executions of `src.bounded_agent.run_bounded_agent()`
against the live Gemini API (no mocking), per the Week 5 "Three execution
traces" deliverable. Each trace is interpreted against the rules in
`docs/requirements/Agent_Task_Contract for week 5.docx`. Full step-by-step
state for each run is in:

- `evidence/traces/week5_bounded_agent_trace.json` (trace 1)
- `evidence/traces/week5_execution_trace_run2_ambiguous_message.json` (trace 2)
- `evidence/traces/week5_execution_trace_run3_model_parsing_failure.json` (trace 3)

## Trace summary

| Trace | Input | Iterations | Stop reason | Contract section |
|---|---|---|---|---|
| 1 | "My power has been out since last night in Ntinda." | 1 | `ticket_drafted_pending_approval` | 5.4 Human Hand-Off |
| 2 | "something is wrong with my service, not sure what exactly" | 1 | `model_parsing_failure` | 5.2 Failure Stop Condition |
| 3 | "My power has been out since this morning, when will it be back?" | 1 | `model_parsing_failure` | 5.2 Failure Stop Condition |

## Trace 1: success path, human hand-off

The model classified the message as `outage`, retrieved 3 correct knowledge-base
sources (KB-001, KB-005, KB-006), called `get_outage_status` (area had no
active outage on record) and `draft_ticket` in the same step, and produced a
draft with `status: "pending_approval"`. The loop stopped immediately after,
matching contract section 5.4: *"Ticket draft created: After draft_ticket is
called; the workflow stops (the draft requires human approval)."* No
autonomous submission occurred — the draft sat in `pending_approval`, as
required by section 2(d)'s tool permission matrix. State was fully populated
(`classification_result`, `retrieved_sources`, `tool_calls_made`,
`tool_results`) and `iteration_count` stopped at 1, well under
`MAX_ITERATIONS = 3`.

## Traces 2 and 3: failure/recovery path (model_parsing_failure)

Both traces hit the same real failure, independently, on two different
messages: the live Gemini response was cut off mid-string
(`finish_reason: "MAX_TOKENS"`) after only 22–24 visible output tokens,
despite `max_output_tokens=600` being set in `src/agent.py`, leaving an
unterminated JSON string that `_parse_model_json()` correctly rejected
(`parsed: None`).

In both cases, `run_bounded_agent()` behaved exactly as the contract
requires: `check_stop_condition()`'s first check — *"5.2 Failure: couldn't
even parse a response"* — caught it, set `stop_reason: "model_parsing_failure"`,
recorded the full trace (including the raw truncated text and the parse
error), and returned cleanly after 1 iteration. No exception propagated, no
crash, no silent loop. This is the required failure/recovery case: something
genuinely went wrong at the model layer, and the bounded workflow handled it
safely rather than hanging, looping to `MAX_ITERATIONS` uselessly, or
returning malformed data as if it were valid.

## Finding: the MAX_TOKENS failure appears systemic, not a one-off

Across four live-model attempts made while producing this evidence (one
ad-hoc smoke test plus traces 1–3, all on the same day), **three of four**
hit the same truncation failure. Both failing traces show a consistent
signature: ~1,900+ input tokens, well under 30 output tokens, and
`finish_reason: "MAX_TOKENS"` — strongly suggesting
`models/gemini-flash-latest` (an alias, not a pinned model version) has
drifted to an underlying model that consumes hidden reasoning/"thinking"
tokens from the same `max_output_tokens` budget, leaving almost nothing for
the actual JSON response. Trace 1's success the same day indicates this is
intermittent rather than a hard block, which makes it more dangerous in
production, not less: it will pass local smoke tests and fail unpredictably
under real traffic.

**Recommendation:** whoever owns `src/agent.py` should either raise
`max_output_tokens` substantially (e.g. to 1500–2000) or pin the model to a
specific stable version string instead of the `-latest` alias, then re-run
the Week 2/4 evaluation suites to check whether this was silently depressing
earlier results too. This is a strong candidate for the Week 7 Failure
Catalogue if not resolved before then, and is worth raising with the team
now rather than waiting.

## Contract conformance observed

- `MAX_ITERATIONS = 3` was never exceeded (all 3 traces stopped at iteration 1).
- No tool was called outside the approved allow-list (section 2c).
- `draft_ticket` never produced anything but `status: "pending_approval"` — no
  autonomous submission was possible or attempted (section 2d).
- Failure handling did not invent facts or fabricate a response when parsing
  failed (section 3.3: "If grounding_status is insufficient_evidence, the
  agent must not invent facts" — extended here to the parsing-failure case,
  where the system correctly returned nothing rather than guessing).

## Known limitations not exercised by these traces

- **Re-planning (section 6.5, 7) was not observed**, because no trace reached
  a second iteration. Separately, `bounded_agent.py`'s loop re-calls
  `call_agent()` with the *original* customer message on every iteration,
  without feeding back prior tool results or state — so even a multi-iteration
  run would not currently perform genuine re-planning as the contract
  describes it. This is a design gap worth flagging for Week 6.
- Several documented stop conditions were not exercised here because no
  trace reached them: grounding mismatch, unauthorized tool calls, all three
  safety conditions (5.3), and the ambiguous-input/emergency hand-off cases
  (5.4). `check_stop_condition()` does not yet implement most of these in
  code, consistent with the gap already noted in the Week 4 evidence doc
  regarding tool-output schema validation (section 3.3), which also remains
  unresolved.
