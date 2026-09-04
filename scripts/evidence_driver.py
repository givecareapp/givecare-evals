#!/usr/bin/env python3
"""Hound protocol adapter for the gc-evals public gold-case corpus.

Hound is the only supported write entry point. The adapter admits one reviewed,
public-safe gold case and deterministically projects the owner split files into
the selected owner split. A separate ``corpus.project`` operation writes
``data/all.jsonl``. It uses only the Python standard library.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
RESPONSE_SCHEMA = "hound.driver.response.v1"
SPLITS = (
    "core-behaviors",
    "red-team",
    "reddit-caregivers",
    "multi-turn",
)
GOLD_CASE_FIELDS = {
    "id",
    "split",
    "category",
    "subcategory",
    "input",
    "expected_behaviors",
    "forbidden_patterns",
    "context",
    "source",
}
ARTIFACT_FIELDS = {
    "schema_version",
    "owner",
    "kind",
    "artifact_id",
    "revision",
    "sha256",
    "access",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TRACE_REF_FIELDS = {"loop_id", "intent_sha256"}
APPLY_CAPABILITY = {
    "name": "evals.gold-cases.apply",
    "effect": "write",
    "gate": "human",
    "adapter": {
        "kind": "hound-operation",
        "ref": "evidence-driver.json#corpus.apply",
    },
    "accepts": ["gc-evals.gold-case-intake/v1"],
    "emits": ["gc-evals.gold-case/v1", "gc-evals.apply-result/v1"],
}


class DriverError(Exception):
    pass


def _response(
    *,
    outcome: str,
    data_schema: str,
    data: dict[str, Any],
    artifacts: list[dict[str, Any]] | None = None,
    proofs: list[dict[str, Any]] | None = None,
    diagnostics: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": RESPONSE_SCHEMA,
        "ok": outcome not in {"held", "failed"},
        "outcome": outcome,
        "data_schema": data_schema,
        "data": data,
        "artifacts": artifacts or [],
        "proofs": proofs or [],
        "diagnostics": diagnostics or [],
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _projection_ref(data: bytes) -> dict[str, str]:
    digest = _sha256(data)
    return {
        "schema_version": "givecare.artifact-ref/v1",
        "owner": "evals.dataset",
        "kind": "owner-projection",
        "artifact_id": "data/all.jsonl",
        "revision": f"sha256:{digest}",
        "sha256": digest,
        "access": "public",
    }


def _effect(root: Path, relative: str, after: bytes) -> dict[str, Any] | None:
    path = root / relative
    before = path.read_bytes() if path.is_file() else None
    before_mode = f"{path.stat().st_mode & 0o7777:04o}" if path.is_file() else "0644"
    if before == after:
        return None
    return {
        "path": relative,
        "mode": before_mode,
        "before_sha256": _sha256(before) if before is not None else None,
        "after_sha256": _sha256(after),
    }


def _read_split_bytes(root: Path) -> dict[str, bytes]:
    values: dict[str, bytes] = {}
    for split in SPLITS:
        path = root / "data" / f"{split}.jsonl"
        if not path.is_file():
            raise DriverError(f"missing canonical split: {path.relative_to(root)}")
        value = path.read_bytes()
        if not value or not value.endswith(b"\n"):
            raise DriverError(
                "canonical split must be non-empty and newline-terminated: "
                f"{path.relative_to(root)}"
            )
        values[split] = value
    return values


def _project(split_bytes: dict[str, bytes]) -> bytes:
    return b"".join(split_bytes[split] for split in SPLITS)


def _load_validator(root: Path):
    validator_path = root / "scripts" / "validate.py"
    spec = importlib.util.spec_from_file_location("gc_evals_validator", validator_path)
    if spec is None or spec.loader is None:
        raise DriverError("cannot load the owner validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _existing_records(root: Path, split_bytes: dict[str, bytes]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for split in SPLITS:
        for line_number, line in enumerate(split_bytes[split].splitlines(), start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise DriverError(
                    f"data/{split}.jsonl:{line_number}: invalid JSON: {error.msg}"
                ) from error
            if not isinstance(value, dict):
                raise DriverError(f"data/{split}.jsonl:{line_number}: record must be an object")
            records.append(value)
    return records


def _require_exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise DriverError(f"{label} must contain exactly {sorted(fields)!r}")
    return value


def _require_nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DriverError(f"{label} must be a non-empty string")
    return value


def _validate_artifact_ref(value: Any, label: str = "artifact ref") -> dict[str, Any]:
    artifact = _require_exact_object(value, ARTIFACT_FIELDS, label)
    if artifact["schema_version"] != "givecare.artifact-ref/v1":
        raise DriverError(f"{label}.schema_version must be givecare.artifact-ref/v1")
    for field in ("owner", "kind", "artifact_id", "revision"):
        _require_nonempty(artifact[field], f"{label}.{field}")
    if not isinstance(artifact["sha256"], str) or not SHA256_RE.fullmatch(artifact["sha256"]):
        raise DriverError(f"{label}.sha256 must be a lowercase SHA-256 digest")
    if artifact["access"] not in {"restricted", "workspace", "public"}:
        raise DriverError(f"{label}.access is invalid")
    return artifact


def _validate_artifact_refs(value: Any, label: str, *, required: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (required and not value):
        suffix = "non-empty " if required else ""
        raise DriverError(f"{label} must be a {suffix}list")
    refs = [_validate_artifact_ref(item, f"{label}[{index}]") for index, item in enumerate(value)]
    canonical = [_canonical_json(item) for item in refs]
    if len(canonical) != len(set(canonical)):
        raise DriverError(f"{label} must not contain duplicate artifact refs")
    return refs


def _validate_shared_trace(value: Any) -> dict[str, Any]:
    protocol_cli = ROOT.parent / "scripts" / "givecare_protocol.py"
    if not protocol_cli.is_file():
        raise DriverError(f"missing shared GiveCare Trace validator: {protocol_cli}")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix="gc-evals-trace-",
            suffix=".json",
            delete=False,
        ) as temporary:
            temporary.write(_canonical_json(value) + b"\n")
            temporary_path = Path(temporary.name)
        result = subprocess.run(
            [
                sys.executable,
                str(protocol_cli),
                "--root",
                str(ROOT.parent),
                "trace",
                str(temporary_path),
                "--show-restricted",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DriverError("shared GiveCare Trace validation could not complete") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise DriverError(f"shared GiveCare Trace validation failed: {detail}")
    try:
        summary = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise DriverError("shared GiveCare Trace validator emitted invalid JSON") from error
    if not isinstance(summary, dict):
        raise DriverError("shared GiveCare Trace validator emitted an invalid summary")
    for field in ("loop_id", "owner", "capability"):
        _require_nonempty(summary.get(field), f"shared Trace {field}")
    if not isinstance(summary.get("intent_sha256"), str) or not SHA256_RE.fullmatch(
        summary["intent_sha256"]
    ):
        raise DriverError("shared Trace intent_sha256 is invalid")
    if summary.get("intent_contract") != APPLY_CAPABILITY:
        raise DriverError(
            "pinned evals.gold-cases.apply must be the exact human-gated Hound capability"
        )
    return summary


def _validate_local_trace(value: Any, shared: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DriverError("trace must be an object")
    intent = value.get("intent")
    if not isinstance(intent, dict):
        raise DriverError("trace.intent must be an object")
    if (
        shared["owner"] != "evals.dataset"
        or shared["capability"] != "evals.gold-cases.apply"
        or intent.get("owner") != shared["owner"]
        or intent.get("capability") != shared["capability"]
    ):
        raise DriverError(
            "trace intent must target evals.dataset / evals.gold-cases.apply"
        )
    if intent.get("loop_id") != shared["loop_id"]:
        raise DriverError("shared Trace loop_id does not match the input Trace")
    if intent.get("access") != "restricted":
        raise DriverError("trace intent access must be restricted")
    if (
        intent.get("action")
        != "Apply one reviewed gold_case change through evals.gold-cases.apply."
    ):
        raise DriverError("trace intent action must bind the gold_case lever")
    input_refs = intent.get("input_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        raise DriverError("trace intent must bind exactly one learning proposal source")
    source = input_refs[0]
    if (
        not isinstance(source, dict)
        or source.get("owner") != "gc-sms.care"
        or source.get("kind") != "learning-proposal-projection"
        or source.get("access") != "restricted"
    ):
        raise DriverError("trace intent source must be the restricted gc-sms proposal")

    receipts = value.get("receipts")
    if not isinstance(receipts, list) or len(receipts) != 1:
        raise DriverError("trace must contain exactly one proposal receipt")
    receipt = receipts[0]
    if (
        not isinstance(receipt, dict)
        or receipt.get("loop_id") != shared["loop_id"]
        or receipt.get("owner") != "gc-sms.care"
        or receipt.get("phase") != "proposal"
        or receipt.get("status") != "completed"
        or receipt.get("operation") != "care.learning.propose"
        or receipt.get("native_ref") != source
        or receipt.get("input_refs") != []
        or receipt.get("output_refs") != [source]
    ):
        raise DriverError("trace must bind the exact completed gc-sms proposal receipt")
    module_refs = value.get("module_refs")
    if not isinstance(module_refs, list):
        raise DriverError("shared Trace module_refs are unavailable")
    return {
        "schema_version": "gc-evals.learning-trace-ref/v1",
        "loop_id": shared["loop_id"],
        "intent_sha256": shared["intent_sha256"],
        "trace_sha256": _sha256(_canonical_json(value)),
        "module_refs": module_refs,
        "intent_contract": shared["intent_contract"],
    }


def _validate_learning_lineage(value: Any) -> dict[str, Any]:
    lineage = _require_exact_object(
        value,
        {"demand_sha256", "trace_refs", "module_refs"},
        "learning_lineage",
    )
    if not isinstance(lineage["demand_sha256"], str) or not SHA256_RE.fullmatch(
        lineage["demand_sha256"]
    ):
        raise DriverError("learning_lineage.demand_sha256 must be a lowercase SHA-256 digest")
    trace_refs = lineage["trace_refs"]
    if not isinstance(trace_refs, list) or len(trace_refs) > 500:
        raise DriverError("learning_lineage.trace_refs must contain at most 500 items")
    trace_keys: set[bytes] = set()
    for index, value in enumerate(trace_refs):
        label = f"learning_lineage.trace_refs[{index}]"
        ref = _require_exact_object(value, TRACE_REF_FIELDS, label)
        _require_nonempty(ref["loop_id"], f"{label}.loop_id")
        if not isinstance(ref["intent_sha256"], str) or not SHA256_RE.fullmatch(
            ref["intent_sha256"]
        ):
            raise DriverError(f"{label}.intent_sha256 must be a lowercase SHA-256 digest")
        encoded = _canonical_json(ref)
        if encoded in trace_keys:
            raise DriverError("learning_lineage.trace_refs must be unique")
        trace_keys.add(encoded)
    module_refs = _validate_artifact_refs(
        lineage["module_refs"], "learning_lineage.module_refs"
    )
    if len(module_refs) > 100:
        raise DriverError("learning_lineage.module_refs must contain at most 100 items")
    return lineage


def _validate_intake(
    root: Path, value: Any
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    payload = _require_exact_object(
        value,
        {"schema_version", "trace", "failure", "release", "gold_case"},
        "corpus.apply input",
    )
    if payload["schema_version"] != "gc-evals.gold-case-intake/v1":
        raise DriverError("corpus.apply input schema_version must be gc-evals.gold-case-intake/v1")

    shared_trace = _validate_shared_trace(payload["trace"])

    failure = _require_exact_object(
        payload["failure"],
        {"kind", "verifier", "observed_failure", "mutable_lever"},
        "failure",
    )
    if failure["kind"] != "verified-behavioral-failure":
        raise DriverError("failure.kind must be verified-behavioral-failure")
    _require_nonempty(failure["verifier"], "failure.verifier")
    _require_nonempty(failure["observed_failure"], "failure.observed_failure")
    if failure["mutable_lever"] != "gold_case":
        raise DriverError("failure.mutable_lever must be gold_case")
    learning = _validate_local_trace(payload["trace"], shared_trace)

    release = _require_exact_object(
        payload["release"],
        {"anonymized", "public_safe", "redistribution_rights"},
        "release",
    )
    if any(release[field] is not True for field in release):
        raise DriverError("all release checks must be true")

    gold_case = payload["gold_case"]
    if not isinstance(gold_case, dict):
        raise DriverError("gold_case must be an object")
    unknown = set(gold_case) - GOLD_CASE_FIELDS
    if unknown:
        raise DriverError(f"gold_case contains unsupported fields: {sorted(unknown)!r}")
    if gold_case.get("split") not in SPLITS:
        raise DriverError(f"gold_case.split must be one of {list(SPLITS)!r}")

    split_bytes = _read_split_bytes(root)
    records = _existing_records(root, split_bytes)
    by_id = {record.get("id"): record for record in records}
    record_id = gold_case.get("id")
    if record_id in by_id:
        if by_id[record_id] != gold_case:
            raise DriverError(f"gold case id already exists with different content: {record_id!r}")
        return payload, gold_case, learning

    validator = _load_validator(root)
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            validator.validate_record(
                root / "data" / f"{gold_case['split']}.jsonl",
                gold_case,
                {str(record.get("id")) for record in records},
            )
    except SystemExit as error:
        detail = stderr.getvalue().strip() or str(error)
        raise DriverError(f"gold_case failed owner validation: {detail}") from error
    return payload, gold_case, learning


def _validate_current_projection(root: Path, split_bytes: dict[str, bytes]) -> None:
    current = root / "data" / "all.jsonl"
    if not current.is_file() or current.read_bytes() != _project(split_bytes):
        raise DriverError("data/all.jsonl is stale; run corpus.project before corpus.apply")


def _apply_plan(root: Path, value: Any) -> dict[str, Any]:
    _payload, gold_case, learning = _validate_intake(root, value)
    split_bytes = _read_split_bytes(root)
    _validate_current_projection(root, split_bytes)
    records = _existing_records(root, split_bytes)
    existing = next((record for record in records if record.get("id") == gold_case.get("id")), None)
    if existing is not None:
        return {
            "schema_version": "gc-evals.apply-plan/v1",
            "gold_case_id": gold_case["id"],
            "expected_effects": [],
            "learning": learning,
        }

    encoded = json.dumps(
        gold_case,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    target = str(gold_case["split"])
    projected_splits = dict(split_bytes)
    projected_splits[target] = split_bytes[target] + encoded
    target_relative = f"data/{target}.jsonl"
    effects = [
        effect
        for effect in (
            _effect(root, target_relative, projected_splits[target]),
        )
        if effect is not None
    ]
    return {
        "schema_version": "gc-evals.apply-plan/v1",
        "gold_case_id": gold_case["id"],
        "gold_case": gold_case,
        "target_split": target,
        "expected_effects": sorted(effects, key=lambda item: item["path"]),
        "next_projection_sha256": _sha256(_project(projected_splits)),
        "learning": learning,
    }


def _project_plan(root: Path, value: Any) -> dict[str, Any]:
    learning_lineage = None
    if value not in ({}, None):
        payload = _require_exact_object(
            value,
            {"schema_version", "learning_lineage"},
            "corpus.project input",
        )
        if payload["schema_version"] != "gc-evals.project-input/v1":
            raise DriverError(
                "corpus.project input schema_version must be gc-evals.project-input/v1"
            )
        learning_lineage = _validate_learning_lineage(payload["learning_lineage"])
    projection = _project(_read_split_bytes(root))
    effect = _effect(root, "data/all.jsonl", projection)
    plan = {
        "schema_version": "gc-evals.project-plan/v1",
        "expected_effects": [] if effect is None else [effect],
        "projection": _projection_ref(projection),
    }
    if learning_lineage is not None:
        plan["learning_lineage"] = learning_lineage
    return plan


def _write_effects(root: Path, plan: dict[str, Any]) -> list[str]:
    written: list[str] = []
    if plan["schema_version"] == "gc-evals.apply-plan/v1" and plan["expected_effects"]:
        target = str(plan["target_split"])
        split_bytes = _read_split_bytes(root)
        encoded = json.dumps(
            plan["gold_case"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        split_bytes[target] += encoded
        outputs = {f"data/{target}.jsonl": split_bytes[target]}
    else:
        outputs = {"data/all.jsonl": _project(_read_split_bytes(root))}

    for effect in plan["expected_effects"]:
        relative = effect["path"]
        data = outputs[relative]
        if _sha256(data) != effect["after_sha256"]:
            raise DriverError(f"approved output digest changed: {relative}")
        path = root / relative
        path.write_bytes(data)
        os.chmod(path, int(effect["mode"], 8))
        written.append(relative)
    return written


def _run_owner_validator(root: Path) -> None:
    validator = _load_validator(root)
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            validator.validate_gold_cases()
    except SystemExit as error:
        detail = stderr.getvalue().strip() or stdout.getvalue().strip() or str(error)
        raise DriverError(f"owner validation failed after write: {detail}") from error


def _run_owner_split_validator(root: Path) -> None:
    validator = _load_validator(root)
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            validator.validate_source_splits()
    except SystemExit as error:
        detail = stderr.getvalue().strip() or stdout.getvalue().strip() or str(error)
        raise DriverError(f"owner split validation failed after write: {detail}") from error


def handle_request(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    mode = request.get("mode")
    operation = request.get("operation")
    value = request.get("input", {})

    if mode == "check":
        return _response(
            outcome="completed",
            data_schema="gc-evals.driver-check/v1",
            data={"protocol": "hound.protocol.v1", "owner": "gc-evals"},
        )

    if operation == "corpus.apply" and mode == "plan":
        plan = _apply_plan(root, value)
        outcome = "planned" if plan["expected_effects"] else "no-change"
        return _response(
            outcome=outcome,
            data_schema="gc-evals.apply-plan/v1",
            data=plan,
            proofs=[{"kind": "gold-case-owner-validator", "passed": True}],
        )

    if operation == "corpus.apply" and mode == "execute":
        plan = _apply_plan(root, value)
        if request.get("driver_plan") != plan:
            raise DriverError("approved corpus plan no longer matches the intake")
        written = _write_effects(root, plan)
        _run_owner_split_validator(root)
        return _response(
            outcome="completed" if written else "no-change",
            data_schema="gc-evals.apply-result/v1",
            data={
                "written": written,
                "next_projection_sha256": plan.get("next_projection_sha256"),
                "learning": plan["learning"],
            },
            proofs=[{"kind": "gold-case-owner-validator", "passed": True}],
        )

    if operation == "corpus.project" and mode == "plan":
        plan = _project_plan(root, value)
        return _response(
            outcome="planned" if plan["expected_effects"] else "no-change",
            data_schema="gc-evals.project-plan/v1",
            data=plan,
            artifacts=[plan["projection"]],
        )

    if operation == "corpus.project" and mode == "execute":
        plan = _project_plan(root, value)
        if request.get("driver_plan") != plan:
            raise DriverError("approved projection plan no longer matches the corpus")
        written = _write_effects(root, plan)
        _run_owner_validator(root)
        data = {"written": written, "projection": plan["projection"]}
        if "learning_lineage" in plan:
            data["learning_lineage"] = plan["learning_lineage"]
        return _response(
            outcome="completed" if written else "no-change",
            data_schema="gc-evals.project-result/v1",
            data=data,
            artifacts=[plan["projection"]],
            proofs=[{"kind": "projection-hash-and-owner-validator", "passed": True}],
        )

    raise DriverError(f"unsupported Hound request: mode={mode!r} operation={operation!r}")


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise DriverError("request must be an object")
        response = handle_request(ROOT, request)
    except (DriverError, json.JSONDecodeError, OSError, UnicodeError, ValueError) as error:
        response = _response(
            outcome="failed",
            data_schema="gc-evals.error/v1",
            data={},
            diagnostics=[f"gc-evals driver: {error}"],
        )
    json.dump(response, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
