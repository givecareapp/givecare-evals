"""Proof that instrument parity requires an exact verified Hound projection."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate.py"
SYNC = ROOT / "scripts" / "sync_instruments.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("gc_evals_validate", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sync():
    spec = importlib.util.spec_from_file_location("gc_evals_sync_instruments", SYNC)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocalOwnerArtifactTests(unittest.TestCase):
    def test_gold_cases_and_instruments_pass_owner_validation(self) -> None:
        validator = load_validator()
        self.assertEqual(validator.validate_gold_cases(), 118)
        validator.validate_instruments()

    def test_module_declares_the_exact_tools_projection_verifier(self) -> None:
        declaration = json.loads(
            (ROOT / ".givecare" / "module.json").read_text(encoding="utf-8")
        )
        capabilities = {
            item["name"]: item for item in declaration["modules"][0]["capabilities"]
        }
        self.assertEqual(
            capabilities["evals.instruments.sync-owner-projection"],
            {
                "name": "evals.instruments.sync-owner-projection",
                "effect": "write",
                "gate": "none",
                "adapter": {
                    "kind": "cli",
                    "ref": (
                        "python3 scripts/sync_instruments.py --run-dir "
                        "<exact-gc-tools-hound-run>"
                    ),
                },
                "accepts": ["givecare.artifact-ref/v1"],
                "emits": ["@givecare/tools.InstrumentExport"],
            },
        )

    def test_public_instrument_view_composes_projection_and_overlay(self) -> None:
        validator = load_validator()
        view = validator.build_instrument_records()

        self.assertEqual({item["name"] for item in view["instruments"]}, {
            "gc_sdoh6", "ema3", "gc_sdoh30"
        })
        self.assertEqual(view["meta"]["version"], "v2")
        self.assertEqual(view["scoring"]["composite"]["domain_weights"]["GC1"], 0.2)

    def test_overlay_does_not_shadow_tools_owner_fields(self) -> None:
        overlay = json.loads(
            (ROOT / "data" / "instruments-overlay.json").read_text(encoding="utf-8")
        )

        self.assertNotIn("version", overlay["meta"])
        self.assertNotIn("domain_weights", overlay["scoring"]["composite"])
        self.assertNotIn("domain_labels", overlay["scoring"]["composite"])
        for package in overlay["instruments"].values():
            self.assertNotIn("name", package)
            self.assertNotIn("questions", package)


class ToolsProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.tools = self.root / "gc-tools"
        self.runs = self.tools / ".hound" / "runs"
        self.run = self.runs / ("1" * 64)
        self.run.mkdir(parents=True)
        (self.tools / "data").mkdir()
        self.export_path = self.tools / "data" / "instruments-export.json"
        self.export = b'{"version":"test"}\n'
        self.export_path.write_bytes(self.export)
        digest = hashlib.sha256(self.export).hexdigest()
        self.protocol = self.root / "givecare_protocol.py"
        self.protocol.write_text(
            "import json\n"
            + "print(json.dumps("
            + repr(
                {
                    "schema_version": "givecare.artifact-ref/v1",
                    "owner": "tools.assessments",
                    "kind": "owner-projection",
                    "artifact_id": "data/instruments-export.json",
                    "revision": f"sha256:{digest}",
                    "sha256": digest,
                    "access": "public",
                }
            )
            + ", sort_keys=True, separators=(',', ':')))\n",
            encoding="utf-8",
        )
        self.validator = load_validator()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def find(self):
        return self.validator.resolve_verified_tools_projection(
            tools_root=self.tools,
            run_dir=self.run,
            protocol_cli=self.protocol,
        )

    def test_accepts_exact_artifact_and_verified_run(self) -> None:
        resolved = self.find()
        self.assertEqual(resolved[0], self.run)
        self.assertEqual(resolved[1], self.export_path)
        self.assertEqual(resolved[2], self.export)

    def test_rejects_same_path_with_a_different_digest(self) -> None:
        self.export_path.write_bytes(self.export + b"drift")
        with self.assertRaisesRegex(
            self.validator.ProjectionError, "does not match"
        ):
            self.find()

    def test_rejects_the_explicit_run_without_searching_history(self) -> None:
        self.protocol.write_text("raise SystemExit(1)\n", encoding="utf-8")
        with self.assertRaisesRegex(
            self.validator.ProjectionError, "shared projection verification failed"
        ):
            self.find()

    def test_sync_materializes_exact_projection_bytes_atomically(self) -> None:
        sync = load_sync()
        target = self.root / "gc-evals" / "data" / "instruments.json"
        target.parent.mkdir(parents=True)

        self.assertTrue(
            sync.materialize(
                run_dir=self.run,
                tools_root=self.tools,
                protocol_cli=self.protocol,
                target=target,
            )
        )
        self.assertEqual(target.read_bytes(), self.export)
        self.assertEqual(target.stat().st_mode & 0o777, 0o644)
        self.assertFalse(
            sync.materialize(
                run_dir=self.run,
                tools_root=self.tools,
                protocol_cli=self.protocol,
                target=target,
            )
        )

    def test_sync_cli_exposes_only_the_exact_run_selector(self) -> None:
        source = SYNC.read_text(encoding="utf-8")

        self.assertIn('parser.add_argument("--run-dir"', source)
        self.assertNotIn("--hound-bin", source)
        self.assertNotIn("--tools-root", source)
        self.assertNotIn("--target", source)

    def test_validator_rejects_materialization_byte_drift(self) -> None:
        validator = load_validator()
        evals = self.root / "gc-evals"
        data = evals / "data"
        data.mkdir(parents=True)
        (data / "instruments.json").write_bytes(self.export + b"drift")
        shared_protocol = self.root / "scripts" / "givecare_protocol.py"
        shared_protocol.parent.mkdir()
        shared_protocol.write_text(self.protocol.read_text(encoding="utf-8"), encoding="utf-8")
        validator.ROOT = evals
        validator.DATA = data

        with self.assertRaisesRegex(SystemExit, "1"):
            validator.check_instrument_parity(tools_run_dir=self.run)


if __name__ == "__main__":
    unittest.main()
