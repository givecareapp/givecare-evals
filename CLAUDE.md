# gc-evals

Type: reference.

Operational map for the public dataset. Rules: [`AGENTS.md`](AGENTS.md). Files and data contract: [`CODEMAP.md`](CODEMAP.md).

Each JSONL record has a stable ID, input, expected behavior, category, and
metadata the validator requires. Keep inputs anonymized and usable without
private GiveCare context.

## Commands

```bash
python3 -m unittest discover -s tests
python3 scripts/validate.py --tools-commit <full-gc-tools-commit>
python3 scripts/project_gold_cases.py     # rebuild data/all.jsonl
python3 scripts/sync_instruments.py --owner-commit <full-gc-tools-commit>
```

`sync_instruments.py` verifies the public `givecare.artifact-ref/v1` and copies its
exact committed bytes to `data/instruments.json`; the validator rejects drift. The
public reader composes it with `data/instruments-overlay.json`.

## Gotchas

- `data/all.jsonl` is generated; never hand-edit it.
- `data/instruments.json` is a byte copy of the Tools projection, not an Evals edit.
- `--tools-commit` must be a full commit reachable in the sibling `gc-tools`.

## Pointers

- Gold-case intake and rebuild: [`docs/evidence.md`](docs/evidence.md).
- `gc-bench` imports the owner projection as candidates and owns execution and
  verdicts. `gc-tools` owns executable scoring semantics.
