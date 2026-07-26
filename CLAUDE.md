# gc-evals

Operational guide for the public dataset. Read `VISION.md` for scope.

## Files

- `data/core-behaviors.jsonl`: core cases.
- `data/red-team.jsonl`: adversarial cases.
- `data/all.jsonl`: generated merged dataset.
- `data/instruments.json`: public instrument records.
- `scripts/validate.py`: schema, IDs, splits, order, and safety checks.
- `CODEMAP.md`: data flow and boundaries.

Each JSONL record has a stable ID, input, expected behavior, category, source,
and metadata required by the validator. Keep inputs anonymized and usable
without private GiveCare context.

```bash
python3 scripts/validate.py
```

Update a source split first, regenerate `data/all.jsonl` through the repository
workflow, then validate. `gc-bench` imports cases as candidates; it owns
execution and verdicts. `gc-tools` owns executable scoring semantics.
