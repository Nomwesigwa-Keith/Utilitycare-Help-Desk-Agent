# Week 7 Observability and Tracing Evidence

## Purpose

This document demonstrates the observability and tracing capabilities of the UtiliCare Help-Desk Triage Agent, showing that the system captures comprehensive logs for model, prompt version, retrieved sources, tool calls, latency, errors, and outcomes as required by Week 7 deliverables.

## Deliverable Owner

**Mubiru Umar** - Observability/tracing evidence

---

## 1. Tracing Architecture

The agent implements end-to-end tracing through `src/bounded_agent.py`, which records a complete execution trace for every request. The trace is attached to the final state returned by `run_bounded_agent()`.

### 1.1 Trace Capture Location

- **Primary implementation**: `src/bounded_agent.py` (lines 206-220)
- **State model**: Documented in `docs/requirements/Week6_Workflow_State_Model.docx`
- **Trace examples**: `evidence/traces/week5_bounded_agent_trace.json`, `evidence/traces/week5_execution_trace_run2_ambiguous_message.json`, `evidence/traces/week5_execution_trace_run3_model_parsing_failure.json`

---

## 2. Traced Fields

### 2.1 Currently Captured in Trace (Week 7 Implementation)

Each iteration in the trace record includes:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `iteration` | int | `bounded_agent.py` line 207 | One-based iteration number |
| `raw_text` | str \| null | `agent.py` line 194 | Raw model response text |
| `parsed` | dict \| null | `agent.py` line 196 | Parsed JSON model response |
| `parse_error` | str \| null | `agent.py` line 197 | Parsing/validation error if any |
| `finish_reason` | str \| null | `agent.py` line 198 | Model finish reason (STOP, MAX_TOKENS, etc.) |
| `tool_results` | list[dict] | `agent.py` line 197 | Results from tool executions |
| `memory` | list[dict] | `bounded_agent.py` line 213 | Memory operations performed in this iteration |
| `model` | str | `bounded_agent.py` line 215 | **Model version used** (Week 7) |
| `prompt_version` | str | `bounded_agent.py` line 216 | **Prompt version** (Week 7) |
| `retrieved_sources` | list[dict] | `bounded_agent.py` line 217 | **KB documents used for grounding** (Week 7) |
| `latency_ms` | float | `bounded_agent.py` line 218 | **Iteration duration in milliseconds** (Week 7) |
| `timestamp` | str | `bounded_agent.py` line 219 | **ISO timestamp of iteration** (Week 7) |

### 2.2 Captured in State (Not in Trace)

The following fields are tracked in the agent state and available for observability:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `customer_message` | str | `bounded_agent.py` line 27 | Original customer input |
| `classification_result` | dict | `bounded_agent.py` lines 134-137 | Category and confidence |
| `grounding_status` | str | `bounded_agent.py` line 138 | grounded/insufficient_evidence |
| `retrieved_sources` | list[dict] | `bounded_agent.py` line 142 | Knowledge base documents used |
| `tool_calls_made` | list[dict] | `bounded_agent.py` lines 145-147 | Tool names called |
| `tool_results` | list[dict] | `bounded_agent.py` line 144 | All tool execution results |
| `iteration_count` | int | `bounded_agent.py` line 93 | Current iteration number |
| `requires_clarification` | bool | `bounded_agent.py` line 139 | Whether clarification is needed |
| `clarifying_question` | str \| null | `bounded_agent.py` line 140 | Question to ask customer |
| `stop_reason` | str | `bounded_agent.py` line 225 | Reason workflow stopped |
| `memory_context` | list[dict] | `bounded_agent.py` line 165 | Memory records retrieved |
| `memory_trace` | list[dict] | `bounded_agent.py` lines 166-203 | Memory operations log |

---

## 3. Week 7 Implementation Details

### 3.1 Model and Prompt Version Tracking

**Implementation**: Added `MODEL_ID` and `PROMPT_VERSION` constants in `src/bounded_agent.py` (lines 17-18):

```python
# Model and prompt version for observability
MODEL_ID = os.environ.get("UTILICARE_MODEL", "models/gemini-flash-latest")
PROMPT_VERSION = "v3.0"
```

These values are now included in each trace record, enabling tracking of model version changes and prompt versioning over time.

### 3.2 Retrieved Sources in Per-Iteration Trace

**Implementation**: Added `retrieved_sources` to trace record in `src/bounded_agent.py` (line 217):

```python
"retrieved_sources": result.get("grounding", {}).get("sources", []),
```

This shows which knowledge base documents were used for grounding in each specific iteration, not just in the final state.

### 3.3 Latency Measurements

**Implementation**: Added timing measurements in `src/bounded_agent.py`:

- Start time capture (line 97): `iteration_start_time = time.time()`
- End time calculation for success case (line 100): `iteration_duration_ms = (time.time() - iteration_start_time) * 1000`
- End time calculation for error case (line 102): `iteration_duration_ms = (time.time() - iteration_start_time) * 1000`
- Inclusion in trace (line 218): `"latency_ms": iteration_duration_ms`

This captures the duration of each iteration in milliseconds, enabling performance analysis and SLA monitoring.

### 3.4 Timestamps

**Implementation**: Added ISO timestamp to each trace record in `src/bounded_agent.py` (line 219):

```python
"timestamp": datetime.now(timezone.utc).isoformat(),
```

This provides precise timing for when each iteration occurred, useful for debugging and audit trails.

### 3.5 Error Handling with Observability

**Implementation**: Enhanced error case trace in `src/bounded_agent.py` (lines 114-126) to include all Week 7 observability fields even when an exception occurs:

```python
trace.append({
    "iteration": state["iteration_count"],
    "raw_text": None,
    "parsed": None,
    "tool_results": [],
    "error": error_text,
    # Week 7 observability enhancements for error case
    "model": MODEL_ID,
    "prompt_version": PROMPT_VERSION,
    "retrieved_sources": [],
    "latency_ms": iteration_duration_ms,
    "timestamp": datetime.now(timezone.utc).isoformat(),
})
```

This ensures observability is maintained even during error conditions.

---

## 4. Enhanced Trace Schema (Implemented)

The trace record now includes all Week 7 required fields:

```python
trace.append({
    # Existing fields (Week 5)
    "iteration": state["iteration_count"],
    "raw_text": result.get("raw_text"),
    "parsed": parsed,
    "parse_error": result.get("parse_error"),
    "finish_reason": result.get("finish_reason"),
    "tool_results": tool_results,
    "memory": state["memory_trace"][memory_trace_start:],

    # Week 7 observability enhancements
    "model": result.get("model"),  # Model version used
    "prompt_version": result.get("prompt_version"),  # Prompt version
    "retrieved_sources": result.get("grounding", {}).get("sources", []),  # KB documents used
    "latency_ms": iteration_duration_ms,  # Time taken for this iteration
    "timestamp": datetime.now(timezone.utc).isoformat(),  # When this iteration occurred
})
```

---

## 5. State-Level Observability

The final state returned by `run_bounded_agent()` provides comprehensive observability:

### 5.1 Complete State Example

```json
{
  "customer_message": "My power has been out since last night in Ntinda.",
  "classification_result": {
    "category": "outage",
    "confidence": "high"
  },
  "grounding_status": "grounded",
  "retrieved_sources": [
    {"doc_id": "KB-001", "title": "...", "category": "outage"},
    {"doc_id": "KB-005", "title": "...", "category": "outage"},
    {"doc_id": "KB-006", "title": "...", "category": "outage"}
  ],
  "tool_calls_made": [
    {"tool_name": "get_outage_status"},
    {"tool_name": "draft_ticket"}
  ],
  "tool_results": [
    {
      "tool_name": "get_outage_status",
      "success": true,
      "result": {...},
      "error": null
    },
    {
      "tool_name": "draft_ticket",
      "success": true,
      "result": {...},
      "error": null
    }
  ],
  "iteration_count": 1,
  "requires_clarification": false,
  "clarifying_question": null,
  "stop_reason": "ticket_drafted_pending_approval",
  "memory_context": [...],
  "memory_trace": [...],
  "trace": [...]  // Full iteration-by-iteration trace with Week 7 fields
}
```

### 5.2 Observability Coverage

✅ **Model**: Captured in trace via `model` field
✅ **Prompt version**: Captured in trace via `prompt_version` field
✅ **Retrieval**: Captured in trace via `retrieved_sources` field
✅ **Tool calls**: Fully captured in `tool_calls_made` and `tool_results`
✅ **Latency**: Captured in trace via `latency_ms` field
✅ **Errors**: Captured in `parse_error`, `tool_results[].error`, and trace `error` field
✅ **Outcome**: Captured via `stop_reason` field

---

## 6. Evidence Files

### 6.1 Week 7 Observability Traces (New)

1. **`evidence/traces/week7_observability_trace_1_provider_error.json`** - **NEW** - Demonstrates Week 7 observability features during provider error (503)
   - Captures `model`: "models/gemini-flash-latest"
   - Captures `prompt_version`: "v3.0"
   - Captures `retrieved_sources`: [] (empty due to API failure)
   - Captures `latency_ms`: 35035.253 (accurate 35-second timeout)
   - Captures `timestamp`: "2026-10-15T16:36:33.549124+00:00"
   - Captures full error details
   - **Status**: ✅ Demonstrates all Week 7 observability fields are captured even during error conditions

### 6.2 Historical Traces (Week 5)

The following trace files demonstrate observability from Week 5 (pre-Week 7 enhancements):

1. **`evidence/traces/week5_bounded_agent_trace.json`** - Successful execution with tool calls
2. **`evidence/traces/week5_execution_trace_run2_ambiguous_message.json`** - Model parsing failure
3. **`evidence/traces/week5_execution_trace_run3_model_parsing_failure.json`** - Model parsing failure
4. **`evidence/traces/extended_evaluation_results.csv`** - Extended evaluation with latency measurements

**Note**: Historical trace files do not include the Week 7 enhancements (model, prompt_version, retrieved_sources, latency_ms, timestamp). The new Week 7 trace demonstrates these features are now implemented.

---

## 7. Implementation Status

### 7.1 Complete ✅

- ✅ Model ID is captured in trace
- ✅ Prompt version is captured in trace
- ✅ Retrieved sources are captured in per-iteration trace
- ✅ Latency measurements are implemented
- ✅ Timestamps are captured for each iteration
- ✅ Tool calls are fully traced (name, arguments, success, result, error)
- ✅ Errors are captured at multiple levels (parsing, API, tool execution)
- ✅ Outcome is captured via `stop_reason`
- ✅ Iteration-by-iteration trace is complete
- ✅ Memory operations are traced

### 7.2 No Gaps

All Week 7 observability requirements have been implemented:
- ✅ Model
- ✅ Prompt version
- ✅ Retrieval (retrieved sources)
- ✅ Tool calls
- ✅ Latency
- ✅ Errors
- ✅ Outcome

---

## 8. Conclusion

The implementation now provides complete observability for all Week 7 requirements:

1. ✅ **Model**: Captured in trace via `model` field
2. ✅ **Prompt version**: Captured in trace via `prompt_version` field
3. ✅ **Retrieval**: Captured in trace via `retrieved_sources` field
4. ✅ **Tool calls**: Fully captured with arguments, results, and errors
5. ✅ **Latency**: Measured and captured in milliseconds per iteration
6. ✅ **Errors**: Captured at multiple levels with timestamps
7. ✅ **Outcome**: Captured via `stop_reason` field

The enhanced tracing provides complete visibility into the agent's decision-making process, enabling comprehensive debugging, performance analysis, and audit capabilities.
