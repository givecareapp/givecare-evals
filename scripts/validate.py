#!/usr/bin/env python3
"""Validate caregiver-evals JSON/JSONL artifacts.

The repo is intentionally dependency-free; this script uses only stdlib Python.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SPLITS = [
    ("core-behaviors", 40),
    ("red-team", 22),
    ("reddit-caregivers", 47),
    ("multi-turn", 9),
]
REQUIRED_RECORD_FIELDS = {
    "id",
    "split",
    "category",
    "subcategory",
    "input",
    "expected_behaviors",
    "forbidden_patterns",
}
EXPECTED_INSTRUMENTS = {"sdoh6", "ema3", "sdoh30"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open() as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(f"{path}:{line_number}: invalid JSON: {exc}")
            if not isinstance(value, dict):
                fail(f"{path}:{line_number}: record must be a JSON object")
            records.append(value)
    return records


def validate_record(path: Path, record: dict[str, Any], ids: set[str]) -> None:
    missing = REQUIRED_RECORD_FIELDS - record.keys()
    if missing:
        fail(f"{path}: {record.get('id', '<missing id>')} missing fields: {sorted(missing)}")

    record_id = record["id"]
    split = record["split"]
    if not isinstance(record_id, str) or not record_id.startswith(f"{split}-"):
        fail(f"{path}: id {record_id!r} must start with split {split!r}")
    if record_id in ids:
        fail(f"duplicate id: {record_id}")
    ids.add(record_id)

    for field in ["category", "subcategory", "input"]:
        if not isinstance(record[field], str) or not record[field].strip():
            fail(f"{path}: {record_id}: {field} must be a non-empty string")

    for field in ["expected_behaviors", "forbidden_patterns"]:
        value = record[field]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            fail(f"{path}: {record_id}: {field} must be a list of strings")



def validate_instruments() -> None:
    path = DATA / "instruments.json"
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON: {exc}")

    instruments = payload.get("instruments")
    if not isinstance(instruments, list):
        fail(f"{path}: instruments must be a list")

    names = {item.get("name") for item in instruments if isinstance(item, dict)}
    if names != EXPECTED_INSTRUMENTS:
        fail(f"{path}: expected instruments {sorted(EXPECTED_INSTRUMENTS)}, got {sorted(names)}")

    for item in instruments:
        if not isinstance(item, dict):
            fail(f"{path}: each instrument must be an object")
        questions = item.get("questions")
        if not isinstance(questions, list) or not questions:
            fail(f"{path}: {item.get('name')}: questions must be a non-empty list")
        for question in questions:
            if not isinstance(question, dict):
                fail(f"{path}: {item.get('name')}: question must be an object")
            for field in ["id", "prompt"]:
                if not isinstance(question.get(field), str) or not question[field].strip():
                    fail(f"{path}: {item.get('name')}: question missing {field}")



def main() -> None:
    if (DATA / "benefits-programs.jsonl").exists():
        fail("data/benefits-programs.jsonl should not live in caregiver-evals; use gc-benefits")

    ids: set[str] = set()
    merged: list[dict[str, Any]] = []
    for split, expected_count in SPLITS:
        path = DATA / f"{split}.jsonl"
        records = read_jsonl(path)
        if len(records) != expected_count:
            fail(f"{path}: expected {expected_count} records, got {len(records)}")
        for record in records:
            if record.get("split") != split:
                fail(f"{path}: {record.get('id')}: split must be {split!r}")
            validate_record(path, record, ids)
        merged.extend(records)

    all_records = read_jsonl(DATA / "all.jsonl")
    if all_records != merged:
        fail("data/all.jsonl must exactly equal split files concatenated in canonical order")

    validate_instruments()
    print(f"ok: {len(all_records)} eval records, {len(EXPECTED_INSTRUMENTS)} instruments")


if __name__ == "__main__":
    main()
