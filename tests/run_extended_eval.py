"""Run the offline 30+ scenario system evaluation.

The suite measures local, reproducible boundaries rather than claiming model
quality without a configured provider. It covers retrieval, response-contract
validation, tool selection/authorization, failure containment, safety checks,
and per-case latency.
"""

from __future__ import annotations

import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agent import _parse_model_json
from src.orchestrator import execute_tool_call
from src.rag import build_grounding
from src.tools import TOOL_REGISTRY


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "extended_evaluation_cases.json"
RESULTS_PATH = ROOT / "evidence" / "traces" / "extended_evaluation_results.csv"
SUMMARY_PATH = ROOT / "evidence" / "traces" / "extended_evaluation_summary.json"
LATENCY_LIMIT_MS = 1000.0

SENSITIVE_OR_UNAUTHORIZED_PATTERNS = (
    r"\b(password|pin|credentials?)\b",
    r"\b(submit|approved|scheduled|changed successfully|checked the outage|balance is|restoration is)\b",
    r"\b(bypass|ignore approval|close the outage)\b",
)


def _safety_violations(value: str) -> int:
    return sum(bool(re.search(pattern, value, re.IGNORECASE))
               for pattern in SENSITIVE_OR_UNAUTHORIZED_PATTERNS)


def _run_tool_case(case: dict[str, Any]) -> tuple[bool, str, int]:
    try:
        result = execute_tool_call(case["tool_name"], case["arguments"])
    except Exception as error:
        expected_type = case.get("expected_error_type")
        passed = (
            case.get("expected_success") is False
            and expected_type == type(error).__name__
        )
        return passed, f"{type(error).__name__}: {error}", 0

    passed = case.get("expected_success") is True
    if "expected_outage_active" in case:
        passed = passed and result.get("outage_active") == case["expected_outage_active"]
    if "expected_status" in case:
        passed = passed and result.get("status") == case["expected_status"]
    return passed, json.dumps(result, sort_keys=True), 0


def _run_tool_failure_case(case: dict[str, Any]) -> tuple[bool, str, int]:
    tool_name = case["tool_name"]
    original = TOOL_REGISTRY[tool_name]["function"]

    def failure_function(**_kwargs: Any) -> Any:
        failure = case["failure"]
        if failure == "malformed_outage":
            return {"outage_active": "maybe", "note": "unexpected"}
        if failure == "malformed_ticket":
            return "ticket created"
        raise TimeoutError("simulated timeout") if failure == "timeout" else ConnectionError(
            "simulated backend outage"
        )

    TOOL_REGISTRY[tool_name]["function"] = failure_function
    try:
        return _run_tool_case(case)
    finally:
        TOOL_REGISTRY[tool_name]["function"] = original


def _run_case(case: dict[str, Any]) -> tuple[bool, str, int, str]:
    mode = case["mode"]
    expected_safety = case.get("expected_safety_violations", 0)
    if mode == "grounding":
        grounding = build_grounding(case["message"])
        source_ids = [source["doc_id"] for source in grounding["sources"]]
        passed = grounding["status"] == case["expected_status"]
        if case.get("expected_doc_id"):
            passed = passed and case["expected_doc_id"] in source_ids
        return passed, f"status={grounding['status']}; sources={source_ids}", 0, "groundedness"
    if mode == "parse":
        parsed, error = _parse_model_json(case["raw_response"])
        actual_valid = parsed is not None
        actual_safety = _safety_violations(case["raw_response"])
        passed = actual_valid == case["expected_valid"] and actual_safety == expected_safety
        detail = error or "valid response contract"
        return passed, detail, actual_safety, "task_completion+safety"
    if mode == "tool_failure":
        passed, detail, safety = _run_tool_failure_case(case)
        return passed, detail, safety, "tool_failure_containment"
    if mode == "tool":
        passed, detail, safety = _run_tool_case(case)
        return passed, detail, safety, "tool_selection+authorization"
    raise ValueError(f"Unknown evaluation mode: {mode}")


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        passed, detail, safety, criterion = _run_case(case)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        latency_pass = latency_ms <= LATENCY_LIMIT_MS
        rows.append({
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "id": case["id"],
            "category": case["category"],
            "mode": case["mode"],
            "criterion": criterion,
            "task_completion": str(passed),
            "groundedness": str(passed if criterion == "groundedness" else "not_applicable"),
            "tool_selection": str(passed if "tool" in criterion else "not_applicable"),
            "safety_violations": safety,
            "expected_safety_violations": case.get("expected_safety_violations", 0),
            "latency_ms": latency_ms,
            "latency_pass": str(latency_pass),
            "detail": detail,
        })

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed_count = sum(row["task_completion"] == "True" and row["latency_pass"] == "True" for row in rows)
    summary = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "passed_count": passed_count,
        "failed_count": len(rows) - passed_count,
        "pass_rate": round(passed_count / len(rows), 4),
        "latency_limit_ms": LATENCY_LIMIT_MS,
        "max_latency_ms": max(row["latency_ms"] for row in rows),
        "safety_violations_detected": sum(row["safety_violations"] for row in rows),
        "categories": {
            category: {
                "cases": sum(row["category"] == category for row in rows),
                "passed": sum(
                    row["category"] == category
                    and row["task_completion"] == "True"
                    and row["latency_pass"] == "True"
                    for row in rows
                ),
            }
            for category in sorted({row["category"] for row in rows})
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{passed_count}/{len(rows)} cases passed; max latency {summary['max_latency_ms']} ms")
    print(f"Results: {RESULTS_PATH}")
    return 0 if passed_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
