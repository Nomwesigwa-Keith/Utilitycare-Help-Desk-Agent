# 37 Scenario Evaluation Dataset and Results

## Scope
![alt text](image.png)

This deliverable contains 37 deterministic scenarios covering:

# Category	Passed	Result
1. Normal requests	8/8	Pass
2. Edge cases	6/6	Pass
3. Incorrect information	6/6	Pass
4. Adversarial inputs	6/6	Pass
5. Tool failures	5/5	Pass
6. Unauthorized actions	6/6	Pass
== | **Total** | **37** |



The dataset is stored in
[`tests/extended_evaluation_cases.json`](../../tests/extended_evaluation_cases.json).
The runner is
[`tests/run_extended_eval.py`](../../tests/run_extended_eval.py). It does not
call an external model, so results remain reproducible and do not confuse
provider failures with evaluation failures.


1. Understanding my test results
Test	Result	What it verifies
test_stops_on_grounded_guidance_no_tools	PASSED	The agent stops when it can provide grounded guidance without using tools.
test_stops_on_ticket_drafted	PASSED	The agent stops after drafting a support ticket.
test_stops_on_iteration_limit	PASSED	The agent stops when it reaches its maximum iteration limit.
- Tests passed: 3
- Tests failed: 0
- Execution time: 1.16 seconds
- Errors: None reported

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

