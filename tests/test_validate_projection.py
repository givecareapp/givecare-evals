"""Public dataset checks require no private workspace or foreign checkout.

The real Git projection integration lives in the workspace protocol suite.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicDatasetTests(unittest.TestCase):
    def test_module_declares_the_exact_tools_projection_verifier(self):
        declaration = json.loads((ROOT / ".givecare/module.json").read_text())
        capabilities = {item["name"]: item for item in declaration["modules"][0]["capabilities"]}
        self.assertEqual(
            capabilities["evals.instruments.sync-owner-projection"],
            {
                "name": "evals.instruments.sync-owner-projection",
                "effect": "write",
                "gate": "none",
                "adapter": {"kind": "owner-projection-sync", "ref": "scripts/sync_instruments.py"},
                "accepts": ["givecare.artifact-ref/v1"],
                "emits": ["@givecare/tools.InstrumentExport"],
            },
        )

    def test_local_public_dataset_and_overlay_remain_valid(self):
        spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts/validate.py")
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        self.assertEqual(validator.validate_gold_cases(), 118)
        validator.validate_instruments()
        view = validator.build_instrument_records()
        self.assertEqual(
            {item["name"] for item in view["instruments"]}, {"gc_sdoh6", "ema3", "gc_sdoh30"}
        )
        self.assertEqual(view["meta"]["version"], "v2")
        self.assertEqual(view["scoring"]["composite"]["domain_weights"]["GC1"], 0.2)
        overlay = json.loads((ROOT / "data/instruments-overlay.json").read_text())
        self.assertNotIn("version", overlay["meta"])
        self.assertNotIn("domain_weights", overlay["scoring"]["composite"])
        self.assertNotIn("domain_labels", overlay["scoring"]["composite"])
        for value in overlay["instruments"].values():
            self.assertFalse({"name", "questions"} & value.keys())


if __name__ == "__main__":
    unittest.main()
