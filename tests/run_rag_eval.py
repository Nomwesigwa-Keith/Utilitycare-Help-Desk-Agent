"""Evaluate Week 3 retrieval without calling an external model service.

Usage: python -m tests.run_rag_eval
Writes evidence/traces/week3_rag_eval_results.csv.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.rag import build_grounding


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "rag_test_cases.json"
RESULTS_PATH = ROOT / "evidence" / "traces" / "week3_rag_eval_results.csv"


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for case in cases:
        grounding = build_grounding(case["question"])
        source_ids = [source["doc_id"] for source in grounding["sources"]]
        expected_doc = case["expected_doc_id"]
        passed = (
            grounding["status"] == case["expected_status"]
            and (expected_doc is None or expected_doc in source_ids)
        )
        rows.append({
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
            "id": case["id"], "type": case["type"], "question": case["question"],
            "expected_status": case["expected_status"], "actual_status": str(grounding["status"]),
            "expected_doc_id": expected_doc or "", "retrieved_doc_ids": ";".join(source_ids),
            "pass": str(passed),
        })

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    passed_count = sum(row["pass"] == "True" for row in rows)
    print(f"{passed_count}/{len(rows)} retrieval cases passed. Results: {RESULTS_PATH}")
    return 0 if passed_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
