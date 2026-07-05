#!/usr/bin/env python3
"""Validate givecare-evals JSON/JSONL artifacts.

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
OVERBROAD_FORBIDDEN_PATTERNS = {
    "decrease",
    "dosage",
    "dose",
    "increase",
    "method",
    "mg",
    "normal",
    "system prompt",
    "my instructions",
    "I was told",
    "bright line",
    "most common",
    "for example",
    "one user",
    "I've heard from",
    "prescribe",
    "recommend",
    "take",
    "tell them",
    "you should",
}
REDDIT_INPUT_DENYLIST = {
    "Rachel",
    "http://",
    "https://",
    "u/",
    "r/",
    "I'm 17",
    "I'm 28",
    "look 50",
    "3 years",
    "11th",
    "lecanemab",
    "lithium orotate",
    "pTau217",
    "since I was 13",
}
HIGH_RISK_CATEGORIES = {
    "authority",
    "boundary",
    "bright-line-off",
    "bright-line-on",
    "crescendo",
    "crisis",
    "harmful-support",
    "identity-manipulation",
    "indirect-harm",
    "jailbreak",
    "prompt-injection",
    "therapy-boundary",
}


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
        if field == "forbidden_patterns":
            for item in value:
                if item in OVERBROAD_FORBIDDEN_PATTERNS:
                    fail(f"{path}: {record_id}: forbidden_patterns contains overbroad literal {item!r}")

    category = record["category"]
    expected_behaviors = record["expected_behaviors"]
    if category in HIGH_RISK_CATEGORIES and not any(item.strip() for item in expected_behaviors):
        fail(f"{path}: {record_id}: high-risk category {category!r} requires expected_behaviors")
    if category == "sms-format" and not any(item.strip() for item in expected_behaviors):
        fail(f"{path}: {record_id}: sms-format records require expected_behaviors")

    if split == "reddit-caregivers":
        input_text = record["input"]
        for marker in REDDIT_INPUT_DENYLIST:
            if marker in input_text:
                fail(f"{path}: {record_id}: reddit input contains disallowed identifying marker {marker!r}")

    if split == "multi-turn":
        context = record.get("context")
        if not isinstance(context, dict):
            fail(f"{path}: {record_id}: multi-turn records require context object")
        prior_state = context.get("prior_state")
        if not isinstance(prior_state, list) or not prior_state:
            fail(f"{path}: {record_id}: context.prior_state must be a non-empty list")
        if not all(isinstance(item, str) and item.strip() for item in prior_state):
            fail(f"{path}: {record_id}: context.prior_state must contain non-empty strings")


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

    scoring = payload.get("scoring")
    if not isinstance(scoring, dict):
        fail(f"{path}: scoring must be an object")
    method = scoring.get("method")
    if not isinstance(method, str) or "inversion" not in method or "higher means lower pressure" not in method:
        fail(f"{path}: scoring.method must document inverted GiveCare Score semantics")
    composite = scoring.get("composite")
    if not isinstance(composite, dict):
        fail(f"{path}: scoring.composite must be an object")
    if composite.get("direction") != "higher_score_lower_pressure":
        fail(f"{path}: scoring.composite.direction must be higher_score_lower_pressure")
    if "below 40" not in str(composite.get("sdoh30_trigger", "")):
        fail(f"{path}: scoring.composite.sdoh30_trigger must document the below-40 trigger")

    for item in instruments:
        if not isinstance(item, dict):
            fail(f"{path}: each instrument must be an object")
        if item.get("name") == "sdoh30" and "inverted" not in str(item.get("cadence", "")):
            fail(f"{path}: sdoh30 cadence must document inverted zone-score trigger semantics")
        questions = item.get("questions")
        if not isinstance(questions, list) or not questions:
            fail(f"{path}: {item.get('name')}: questions must be a non-empty list")
        for question in questions:
            if not isinstance(question, dict):
                fail(f"{path}: {item.get('name')}: question must be an object")
            for field in ["id", "prompt"]:
                if not isinstance(question.get(field), str) or not question[field].strip():
                    fail(f"{path}: {item.get('name')}: question missing {field}")


def _project_shared_instruments(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the SHARED instrument fields that gc-tools owns: per-instrument
    ordered (id, prompt, zone?) questions plus composite zone weights. Packaging
    fields this repo owns for distribution (titles, descriptions, cadence,
    license notes, band labels, prose scoring narrative) are intentionally left
    out of parity."""
    instruments: dict[str, list[dict[str, str]]] = {}
    for item in payload.get("instruments", []):
        questions = []
        for q in item.get("questions", []):
            entry = {"id": q.get("id"), "prompt": q.get("prompt")}
            if "zone" in q:
                entry["zone"] = q["zone"]
            questions.append(entry)
        instruments[item.get("name")] = questions
    zone_weights = payload.get("scoring", {}).get("composite", {}).get("zone_weights", {})
    return {"instruments": instruments, "zoneWeights": zone_weights}


def _report_parity_diff(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    exp_i, act_i = expected["instruments"], actual["instruments"]
    for name in sorted(set(exp_i) | set(act_i)):
        want, got = exp_i.get(name), act_i.get(name)
        if want == got:
            continue
        if want is None or got is None:
            print(
                f"  instrument {name!r}: gc-tools={'present' if want else 'absent'} "
                f"evals={'present' if got else 'absent'}",
                file=sys.stderr,
            )
            continue
        for idx in range(max(len(want), len(got))):
            w = want[idx] if idx < len(want) else None
            g = got[idx] if idx < len(got) else None
            if w != g:
                print(f"  {name} q[{idx}]: gc-tools={w} evals={g}", file=sys.stderr)
    if expected["zoneWeights"] != actual["zoneWeights"]:
        print(
            f"  zoneWeights: gc-tools={expected['zoneWeights']} "
            f"evals={actual['zoneWeights']}",
            file=sys.stderr,
        )


def check_instrument_parity() -> None:
    """Gate data/instruments.json's SHARED instrument fields against the canonical
    gc-tools export. gc-tools owns the SDOH instrument definition; this repo
    distributes it. Compare when the sibling export exists; skip with a notice
    when absent (mirrors gc-sms `check-web-contracts`). This repo stays
    dependency-free — plain JSON comparison, no gc-tools import."""
    export_path = ROOT.parent / "gc-tools" / "data" / "instruments-export.json"
    if not export_path.exists():
        print("note: gc-tools sibling export not found; skipping instrument parity check")
        return

    try:
        export = json.loads(export_path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{export_path}: invalid JSON: {exc}")

    payload = json.loads((DATA / "instruments.json").read_text())
    expected = {"instruments": export["instruments"], "zoneWeights": export["zoneWeights"]}
    actual = _project_shared_instruments(payload)
    if actual != expected:
        _report_parity_diff(expected, actual)
        fail(
            "data/instruments.json shared fields diverge from the canonical gc-tools "
            "export (gc-tools owns the definition; align this file to it)"
        )
    print("ok: instrument parity with gc-tools export")


def main() -> None:
    if (DATA / "benefits-programs.jsonl").exists():
        fail("data/benefits-programs.jsonl should not live in givecare-evals; use gc-benefits")

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
    check_instrument_parity()
    print(f"ok: {len(all_records)} eval records, {len(EXPECTED_INSTRUMENTS)} instruments")


if __name__ == "__main__":
    main()
