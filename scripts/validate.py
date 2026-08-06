#!/usr/bin/env python3
"""Validate givecare-evals JSON/JSONL artifacts.

The repo is intentionally dependency-free; this script uses only stdlib Python.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SPLITS = [
    "core-behaviors",
    "red-team",
    "reddit-caregivers",
    "multi-turn",
]
MINIMUM_SPLIT_COUNTS = {
    "core-behaviors": 40,
    "red-team": 22,
    "reddit-caregivers": 47,
    "multi-turn": 9,
}
REQUIRED_RECORD_FIELDS = {
    "id",
    "split",
    "category",
    "subcategory",
    "input",
    "expected_behaviors",
    "forbidden_patterns",
}
EXPECTED_INSTRUMENTS = {"gc_sdoh6", "ema3", "gc_sdoh30"}
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


class ProjectionError(Exception):
    pass


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
    payload = build_instrument_records()
    path = DATA / "instruments-overlay.json"

    instruments = payload["instruments"]
    names = {item["name"] for item in instruments}
    if names != EXPECTED_INSTRUMENTS:
        fail(f"{path}: expected instruments {sorted(EXPECTED_INSTRUMENTS)}, got {sorted(names)}")

    scoring = payload["scoring"]
    method = scoring.get("method")
    if not isinstance(method, str) or "GC-SDOH-6" not in method or "EMA-3 reading" not in method:
        fail(f"{path}: scoring.method must distinguish the structural score from the EMA-3 reading")
    composite = scoring.get("composite")
    if not isinstance(composite, dict):
        fail(f"{path}: scoring.composite must be an object")
    if composite.get("direction") != "higher_score_lower_pressure":
        fail(f"{path}: scoring.composite.direction must be higher_score_lower_pressure")
    if "below 40" not in str(composite.get("sdoh30_trigger", "")):
        fail(f"{path}: scoring.composite.sdoh30_trigger must document the below-40 trigger")
    ema_reading = scoring.get("ema_reading")
    if not isinstance(ema_reading, dict) or ema_reading.get("instrument") != "ema3":
        fail(f"{path}: scoring.ema_reading must identify the EMA-3 reading")

    for item in instruments:
        if item["name"] == "gc_sdoh30" and "below 40" not in str(item.get("cadence", "")):
            fail(f"{path}: gc_sdoh30 cadence must document the below-40 domain trigger")
        questions = item["questions"]
        if not questions:
            fail(f"{path}: {item['name']}: questions must be a non-empty list")
        for question in questions:
            for field in ["id", "prompt"]:
                if not isinstance(question.get(field), str) or not question[field].strip():
                    fail(f"{path}: {item['name']}: question missing {field}")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path}: invalid JSON: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path}: root must be an object")
    return payload

def build_instrument_records() -> dict[str, Any]:
    """Compose the public Evals view from one imported owner projection and overlay."""
    materialization_path = DATA / "instruments.json"
    overlay_path = DATA / "instruments-overlay.json"
    materialization = _read_json_object(materialization_path)
    overlay = _read_json_object(overlay_path)
    if set(materialization) != {
        "note",
        "version",
        "instruments",
        "domainWeights",
        "domainLabels",
    }:
        fail(f"{materialization_path}: invalid owner projection shape")
    if set(overlay) != {"schema_version", "meta", "instruments", "scoring"}:
        fail(f"{overlay_path}: invalid overlay shape")
    if overlay["schema_version"] != "gc-evals.instrument-overlay/v1":
        fail(f"{overlay_path}: invalid schema_version")
    shared = materialization["instruments"]
    packaging = overlay["instruments"]
    if not isinstance(shared, dict) or not isinstance(packaging, dict):
        fail("instrument materialization and overlay must contain instrument objects")
    if set(shared) != EXPECTED_INSTRUMENTS or set(packaging) != EXPECTED_INSTRUMENTS:
        fail("instrument materialization and overlay must name the same expected instruments")

    records: list[dict[str, Any]] = []
    for name, questions in shared.items():
        package = packaging[name]
        if not isinstance(questions, list) or not isinstance(package, dict):
            fail(f"{name}: owner questions and packaging must have valid types")
        package = copy.deepcopy(package)
        if set(package) & {"name", "questions"}:
            fail(f"{overlay_path}: {name} shadows owner instrument fields")
        question_overlays = package.pop("question_overlays", {})
        if not isinstance(question_overlays, dict):
            fail(f"{overlay_path}: {name}.question_overlays must be an object")
        question_ids = {
            question.get("id") for question in questions if isinstance(question, dict)
        }
        if set(question_overlays) - question_ids:
            fail(f"{overlay_path}: {name}.question_overlays contains unknown question ids")
        merged_questions: list[dict[str, Any]] = []
        for question in questions:
            if not isinstance(question, dict) or set(question) - {"id", "prompt", "gcDomain"}:
                fail(f"{materialization_path}: {name} has an invalid owner question")
            extras = question_overlays.get(question.get("id"), {})
            if not isinstance(extras, dict) or set(extras) & {"id", "prompt", "gcDomain"}:
                fail(f"{overlay_path}: {name} question overlay shadows owner fields")
            merged_questions.append({**question, **extras})
        records.append({"name": name, **package, "questions": merged_questions})

    meta = overlay["meta"]
    scoring = copy.deepcopy(overlay["scoring"])
    if not isinstance(meta, dict) or not isinstance(scoring, dict):
        fail(f"{overlay_path}: meta and scoring must be objects")
    if "version" in meta:
        fail(f"{overlay_path}: meta.version belongs only to the owner projection")
    composite = scoring.get("composite")
    if not isinstance(composite, dict):
        fail(f"{overlay_path}: scoring.composite must be an object")
    if "domain_weights" in composite or "domain_labels" in composite:
        fail(f"{overlay_path}: shared domain fields belong only to the owner projection")
    composite["domain_weights"] = materialization["domainWeights"]
    composite["domain_labels"] = materialization["domainLabels"]
    return {
        "meta": {**meta, "version": materialization["version"]},
        "instruments": records,
        "scoring": scoring,
    }


def resolve_verified_tools_projection(
    *,
    tools_root: Path,
    run_dir: Path,
    protocol_cli: Path,
) -> tuple[Path, Path, bytes]:
    """Resolve one exact projection through the shared protocol verifier."""
    if not protocol_cli.is_file():
        raise ProjectionError(f"missing shared projection verifier: {protocol_cli}")
    verification = subprocess.run(
        [
            sys.executable,
            str(protocol_cli),
            "--root",
            str(ROOT.parent),
            "projection-ref",
            "--run-dir",
            str(run_dir),
            "--owner-repo",
            "gc-tools",
            "--driver-id",
            "gc-tools-instruments",
            "--artifact-owner",
            "tools.assessments",
            "--artifact-id",
            "data/instruments-export.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if verification.returncode != 0:
        detail = verification.stderr.strip() or verification.stdout.strip()
        raise ProjectionError(f"shared projection verification failed: {detail}")
    try:
        artifact_ref = json.loads(verification.stdout)
    except json.JSONDecodeError as error:
        raise ProjectionError("shared projection verifier emitted invalid JSON") from error
    if not isinstance(artifact_ref, dict):
        raise ProjectionError("shared projection verifier did not emit an ArtifactRef")
    artifact_id = artifact_ref.get("artifact_id")
    if not isinstance(artifact_id, str):
        raise ProjectionError("verified ArtifactRef has no artifact_id")
    owner_root = tools_root.resolve()
    projection_path = (owner_root / artifact_id).resolve()
    if projection_path == owner_root or owner_root not in projection_path.parents:
        raise ProjectionError("verified ArtifactRef escapes the gc-tools owner repo")
    if not projection_path.is_file():
        raise ProjectionError("verified owner projection is not a readable file")
    export_bytes = projection_path.read_bytes()
    digest = hashlib.sha256(export_bytes).hexdigest()
    expected_ref = {
        "schema_version": "givecare.artifact-ref/v1",
        "owner": "tools.assessments",
        "kind": "owner-projection",
        "artifact_id": "data/instruments-export.json",
        "revision": f"sha256:{digest}",
        "sha256": digest,
        "access": "public",
    }
    if artifact_ref != expected_ref:
        raise ProjectionError("verified ArtifactRef does not match the owner projection bytes")
    return run_dir, projection_path, export_bytes


def check_instrument_parity(*, tools_run_dir: Path) -> None:
    """Require the exact verified Hound projection owned by gc-tools."""
    tools_root = ROOT.parent / "gc-tools"
    protocol_cli = ROOT.parent / "scripts" / "givecare_protocol.py"
    try:
        verified_run, export_path, export_bytes = resolve_verified_tools_projection(
            tools_root=tools_root,
            run_dir=tools_run_dir,
            protocol_cli=protocol_cli,
        )
    except (ProjectionError, OSError, subprocess.TimeoutExpired) as error:
        fail(str(error))

    materialization = (DATA / "instruments.json").read_bytes()
    if materialization != export_bytes:
        fail(
            "data/instruments.json is not the exact byte-for-byte materialization of "
            "the verified gc-tools Hound projection; run scripts/sync_instruments.py"
        )
    print(
        "ok: instrument parity with verified gc-tools Hound projection "
        f"{verified_run.name}"
    )


def validate_source_splits() -> tuple[int, list[dict[str, Any]]]:
    if (DATA / "benefits-programs.jsonl").exists():
        fail("data/benefits-programs.jsonl should not live in givecare-evals; use gc-benefits")

    ids: set[str] = set()
    merged: list[dict[str, Any]] = []
    for split in SPLITS:
        path = DATA / f"{split}.jsonl"
        records = read_jsonl(path)
        if len(records) < MINIMUM_SPLIT_COUNTS[split]:
            fail(
                f"{path}: expected at least {MINIMUM_SPLIT_COUNTS[split]} records, "
                f"got {len(records)}"
            )
        for record in records:
            if record.get("split") != split:
                fail(f"{path}: {record.get('id')}: split must be {split!r}")
            validate_record(path, record, ids)
        merged.extend(records)
    return len(merged), merged


def validate_gold_cases() -> int:
    record_count, merged = validate_source_splits()

    all_records = read_jsonl(DATA / "all.jsonl")
    if all_records != merged:
        fail("data/all.jsonl must exactly equal split files concatenated in canonical order")
    return record_count


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate GiveCare Evals owner artifacts.")
    parser.add_argument(
        "--tools-run-dir",
        type=Path,
        required=True,
        help="exact verified gc-tools corpus.project run directory",
    )
    args = parser.parse_args(argv)
    record_count = validate_gold_cases()

    validate_instruments()
    check_instrument_parity(tools_run_dir=args.tools_run_dir)
    print(f"ok: {record_count} eval records, {len(EXPECTED_INSTRUMENTS)} instruments")


if __name__ == "__main__":
    main()
