"""Small, local case-history store for repeat help-desk reports.

Memory is advisory context for the human agent. It is never included in the
model prompt and stores no raw customer message or personal information.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY_PATH = Path(
    os.environ.get("UTILITYCARE_MEMORY_PATH", str(ROOT / "data" / "case_memory.json"))
).resolve()
RETENTION_DAYS = 30
MAX_RECORDS = 100
VALID_SERVICES = frozenset({"electricity", "water"})
REQUIRED_FIELDS = (
    "draft_id",
    "area_code",
    "service_type",
    "category",
    "summary",
    "created_at",
    "status",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_records() -> list[dict[str, Any]]:
    if not MEMORY_PATH.exists():
        return []
    try:
        value = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read case memory: {error}") from error
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise RuntimeError("Case memory must contain a JSON array of records")
    return value


def _write_records(records: list[dict[str, Any]]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix=f"{MEMORY_PATH.name}.", suffix=".tmp", dir=MEMORY_PATH.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
            file.write("\n")
        os.replace(temporary_path, MEMORY_PATH)
    except OSError as error:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise RuntimeError(f"Could not write case memory: {error}") from error


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("created_at must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("created_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict) or any(field not in record for field in REQUIRED_FIELDS):
        raise ValueError(f"case record must contain: {', '.join(REQUIRED_FIELDS)}")
    for field in ("draft_id", "area_code", "category", "summary", "created_at", "status"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    if record["service_type"] not in VALID_SERVICES:
        raise ValueError("service_type must be 'electricity' or 'water'")
    if record["status"] != "pending_approval":
        raise ValueError("case memory only stores pending_approval drafts")
    _parse_timestamp(record["created_at"])
    return {field: record[field] for field in REQUIRED_FIELDS}


def purge_expired() -> int:
    """Remove expired records and enforce the fixed capacity limit."""
    records = _read_records()
    cutoff = _now() - timedelta(days=RETENTION_DAYS)
    active = []
    for record in records:
        try:
            if _parse_timestamp(record.get("created_at", "")) >= cutoff:
                active.append(record)
        except (TypeError, ValueError):
            continue
    active.sort(key=lambda item: item["created_at"])
    kept = active[-MAX_RECORDS:]
    removed = len(records) - len(kept)
    if removed or (MEMORY_PATH.exists() and kept != records):
        _write_records(kept)
    return removed


def save_case(record: dict[str, Any]) -> dict[str, Any]:
    """Persist one successful ticket draft and return the stored record."""
    stored = _validate_record(record)
    purge_expired()
    records = _read_records()
    records.append(stored)
    _write_records(records[-MAX_RECORDS:])
    return stored


def find_similar(area_code: str, service_type: str) -> list[dict[str, Any]]:
    """Return unexpired cases with an exact area and service match."""
    if not isinstance(area_code, str) or not area_code.strip():
        raise ValueError("area_code must be a non-empty string")
    if service_type not in VALID_SERVICES:
        raise ValueError("service_type must be 'electricity' or 'water'")
    purge_expired()
    return [
        record for record in _read_records()
        if record.get("area_code", "").upper() == area_code.upper()
        and record.get("service_type") == service_type
    ]


def delete_case(draft_id: str) -> bool:
    """Delete one case by draft ID; return whether a record was removed."""
    if not isinstance(draft_id, str) or not draft_id.strip():
        raise ValueError("draft_id must be a non-empty string")
    records = _read_records()
    remaining = [record for record in records if record.get("draft_id") != draft_id]
    if len(remaining) == len(records):
        return False
    _write_records(remaining)
    return True


def clear() -> None:
    """Delete all locally persisted case history."""
    if MEMORY_PATH.exists():
        try:
            MEMORY_PATH.unlink()
        except OSError as error:
            raise RuntimeError(f"Could not clear case memory: {error}") from error
