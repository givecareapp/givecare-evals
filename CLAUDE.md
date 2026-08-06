# gc-evals

Operational guide for the public dataset. Read `VISION.md` for scope.

## Files

- `data/core-behaviors.jsonl`: core cases.
- `data/red-team.jsonl`: adversarial cases.
- `data/all.jsonl`: generated merged dataset.
- `data/instruments.json`: exact materialization of the verified Tools projection.
- `data/instruments-overlay.json`: Evals-only public packaging fields.
- `hound-driver.json`: Hound-owned gold-case intake and projection operations.
- `scripts/validate.py`: schema, IDs, splits, order, and safety checks.
- `CODEMAP.md`: data flow and boundaries.

Each JSONL record has a stable ID, input, expected behavior, category, source,
and metadata required by the validator. Keep inputs anonymized and usable
without private GiveCare context.

```bash
python3 scripts/validate.py --tools-run-dir <exact-gc-tools-hound-run>
```

Use Hound for every gold-case write. `corpus.apply` accepts one verified,
public-safe intake and requires human approval. It updates only the selected
owner split. Run `corpus.project` next. That operation alone writes
`data/all.jsonl` and emits its `givecare.artifact-ref/v1` digest. See
`docs/hound.md`.

`gc-bench` imports only that owner projection as candidates. It owns execution
and verdicts. `gc-tools` owns executable scoring semantics.

Materialize one exact Tools projection before validation:

```bash
python3 scripts/sync_instruments.py --run-dir <exact-gc-tools-hound-run>
```

The command verifies the public `givecare.artifact-ref/v1` and copies its exact
bytes to `data/instruments.json`. The validator rejects any drift. The public
reader composes that materialization with `data/instruments-overlay.json`.
The declared consumer boundary is `evals.instruments.sync-owner-projection`.
