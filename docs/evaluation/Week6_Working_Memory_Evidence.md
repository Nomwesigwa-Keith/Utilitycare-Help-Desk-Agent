# Week 6 Working Memory Evidence

## Scope

This evidence covers persistent case memory across process boundaries and
confirms that recalled memory remains advisory to the bounded workflow.

## Implementation

- [src/memory.py](../../src/memory.py) stores minimal pending-ticket metadata
  in a local JSON file.
- `UTILITYCARE_MEMORY_PATH` allows isolated test storage without changing the
  default runtime location.
- [src/bounded_agent.py](../../src/bounded_agent.py) performs exact
  area/service lookups after the model call and records memory operations in
  the execution trace. Memory is never added to the model prompt.
- [tests/test_week6_working_memory.py](../../tests/test_week6_working_memory.py)
  contains the repeatable evidence tests.

## Test design and evidence

`test_memory_survives_a_new_process` starts one Python interpreter to call
`save_case`, then a separate interpreter to call `find_similar`. The second
process reads the same temporary JSON file and asserts that
`week6-demo-001` is returned. This test passed.

`test_memory_is_useful_but_does_not_bypass_approval` seeds a misleading
historical summary, runs the existing `run_bounded_agent` entry point with a
mocked model result, and asserts all of the following:

- the historical draft is present in `memory_context`;
- the current workflow stops at `ticket_drafted_pending_approval`;
- the current draft remains `pending_approval`;
- no `submit_ticket` action appears in the executed tool calls;
- the trace contains both the lookup match and the new draft write. This test
passed.

`test_second_run_reuses_context_without_copying_decision` performs the save
and recall in separate subprocesses and records the recalled draft ID and
context while keeping the current request as separate evidence. This test passed.

## Commands and results

The following commands were run using Python 3.12.10 from the project virtual
environment:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_week6_working_memory.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_bounded_agent_mock.py -v
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m tests.test_failure_authorization
```

Observed results:

```text
Week 6 working memory: 3 passed
Bounded-agent regression: 3 passed
Full pytest suite: 9 passed
Authorization/failure regression: 8 boundary-held, 2 pre-existing output-schema gaps
```

The full pytest run discovered the 3 bounded-agent tests, 3 Week 6 tests, and
3 tool tests. The authorization script also confirmed that unknown tools and
attempts to submit a draft directly remain blocked. Its two reported gaps are
pre-existing malformed-tool-output validation issues unrelated to Week 6
memory.

The command
`.\.venv\Scripts\python.exe -m pytest tests/run_week5_execution_traces.py -v`
was also checked. It collected zero tests and exited with pytest status 5
because that file is a standalone live-API trace generator, not a pytest test
module. It was compiled successfully with `py_compile`; it was not run against
the live API because that would require an API key and external service
access.

All changed Python files compile successfully, and `git diff --check` passes.

## Limitations

The existing draft tool schema does not require an explicit `service_type`.
The bounded workflow uses the service type from a same-request
`get_outage_status` call when available, and otherwise derives it only for
the existing specific categories `power_outage` and `water_leak`. Drafts
without a defensible service type are not persisted, preventing ambiguous
memory links.
