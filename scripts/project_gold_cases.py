#!/usr/bin/env python3
"""Regenerate data/all.jsonl from the four canonical gold-case splits.

Concatenates the split files in the fixed canonical order (see ``SPLITS`` in
``scripts/validate.py``), writes the result to ``data/all.jsonl``, then runs
the owner split/order checks against it. Run this after editing a split
file, inspect the diff, then commit on `main`.

Consumers never run this script. They pin the committed bytes through the
workspace `projection-ref` command (capability `evals.gold-cases.project`)
and verify the digest.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate import DATA, SPLITS, validate_gold_cases  # noqa: E402


def main() -> None:
    merged = b"".join((DATA / f"{split}.jsonl").read_bytes() for split in SPLITS)
    target = DATA / "all.jsonl"
    target.write_bytes(merged)
    record_count = validate_gold_cases()
    print(f"ok: wrote {target} ({record_count} records)")


if __name__ == "__main__":
    main()
