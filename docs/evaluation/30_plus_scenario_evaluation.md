# 30+ Scenario Evaluation Dataset and Results

## Scope

This deliverable contains 37 deterministic scenarios covering:

| Category | Cases |
| --- | ---: |
| Normal | 8 |
| Edge | 6 |
| Incorrect information | 6 |
| Adversarial | 6 |
| Tool failure | 5 |
| Unauthorized action | 6 |
| **Total** | **37** |

The dataset is stored in
[`tests/extended_evaluation_cases.json`](../../tests/extended_evaluation_cases.json).
The runner is
[`tests/run_extended_eval.py`](../../tests/run_extended_eval.py). It does not
call an external model, so results remain reproducible and do not confuse
provider failures with evaluation failures.

## Measurable criteria

- **Task completion:** the local response parser, tool boundary, or retrieval
  operation matches the scenario oracle.
- **Groundedness:** retrieval returns the expected controlled-source status and,
  where specified, the expected source document.
- **Tool selection and authorization:** approved tools execute with valid
  arguments; unknown tools, missing parameters, unsupported values, and
  unauthorized side-effect arguments are rejected.
- **Tool failure containment:** simulated connection failures, timeouts, and
  malformed tool responses become explicit `ToolExecutionError` results.
- **Safety violations:** the evaluator flags unsupported account facts,
  unauthorized completion claims, credential requests, and approval bypasses.
- **Latency:** every local case must complete within 1,000 ms.

Each CSV row records the case category, criterion, pass/fail result, detected
safety violations, latency, and diagnostic detail. The JSON summary reports
the aggregate pass rate and category totals.

## Run and inspect results

```text
python -m tests.run_extended_eval
```

Generated evidence:

- [`extended_evaluation_results.csv`](../../evidence/traces/extended_evaluation_results.csv)
- [`extended_evaluation_summary.json`](../../evidence/traces/extended_evaluation_summary.json)

The malformed-output scenarios also validate the output contract in
[`src/orchestrator.py`](../../src/orchestrator.py): a tool result must have
the documented fields and types, and ticket drafts must remain
`pending_approval`.
