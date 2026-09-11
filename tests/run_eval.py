"""Run the prompt-evaluation cases against the configured Gemini model.

Usage: python -m tests.run_eval
Writes tests/eval_results.csv and exits non-zero if any case fails or the
model returns an unusable response.
"""

from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from src.agent import call_agent


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "test_cases.json"
RESULTS_PATH = ROOT / "tests" / "eval_results.csv"


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    timestamp = datetime.now(timezone.utc).isoformat()
    def evaluate_case(case: dict[str, str]) -> dict[str, str]:
        try:
            result = call_agent(case["message"])
            parsed = result.get("parsed") or {}
            actual = parsed.get("category") if isinstance(parsed, dict) else None
            parse_error = result.get("parse_error") or ""
            raw_response = result.get("raw_text") or ""
        except Exception as error:  # Record live API failures instead of losing the whole run.
            actual = None
            parse_error = f"{type(error).__name__}: {error}"
            raw_response = ""
        passed = actual == case["expected_category"]
        return {
            "evaluated_at_utc": timestamp,
            "id": case["id"],
            "message": case["message"],
            "expected_category": case["expected_category"],
            "actual_category": actual or "",
            "pass": str(passed),
            "parse_error": parse_error,
            "raw_response": raw_response,
        }

    results: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=len(cases)) as executor:
        futures = [executor.submit(evaluate_case, case) for case in cases]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["id"])

    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    passed_count = sum(row["pass"] == "True" for row in results)
    print(f"{passed_count}/{len(results)} cases passed. Results: {RESULTS_PATH}")
    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
