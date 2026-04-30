# caregiver-evals

Pure public dataset repo. No runtime package — just versioned evaluation records and public SDOH instruments, published to HuggingFace.

## Repo

`givecareapp/caregiver-evals` — public caregiver AI safety evaluation dataset (CC-BY-4.0).

## Scope

Included:

- Caregiver AI safety/quality eval cases
- Red-team and boundary scenarios
- Adapted public caregiver scenarios
- Multi-turn continuity scenarios
- Public GiveCare SDOH instruments: SDOH-6, EMA-3, SDOH-30

Excluded:

- Benefits program catalog (canonical owner: `../gc-benefits`)
- Mira runtime/prompts/private traces
- Production benchmark runner/scoring harness (canonical owner: `../gc-bench`)
- CWBS-14 redistribution material pending original-author licensing confirmation

## What's here

```text
data/
  all.jsonl               # merged dataset (all eval splits)
  core-behaviors.jsonl    # 40 functional tests
  red-team.jsonl          # 22 adversarial attacks
  reddit-caregivers.jsonl # 47 realistic caregiver scenarios adapted from public posts
  multi-turn.jsonl        # 9 stateful conversation scenarios
  instruments.json        # 3 public caregiver SDOH assessment instruments
scripts/
  convert-yaml-to-jsonl.ts # optional YAML -> JSONL conversion utility
  validate.py              # dependency-free dataset validator
```

## Record format

```jsonc
{
  "id": "reddit-caregivers-007",
  "split": "reddit-caregivers",
  "category": "crisis-adjacent",
  "subcategory": "...",
  "input": "caregiver message text",
  "expected_behaviors": ["..."],
  "forbidden_patterns": ["..."]
}
```

## Validation

```bash
python3 scripts/validate.py
```

Checks:

- split counts: 40/22/47/9
- required fields and duplicate IDs
- `data/all.jsonl` exactly equals canonical split concatenation
- `data/instruments.json` contains only `sdoh6`, `ema3`, `sdoh30`
- stale `data/benefits-programs.jsonl` has not been reintroduced

## Relationship to other repos

- `../gc-bench` consumes/evolves benchmark scenarios and scoring harnesses.
- `../gc-sms/packages/evals` may hold private/source Promptfoo YAMLs for internal evaluation.
- `../gc-benefits` owns benefits data; do not add benefits records here.
- `../gc-tools` owns the public TypeScript implementation for the SDOH instruments and scoring.

## Updating eval cases

1. Edit the appropriate split file in `data/*.jsonl`.
2. Update `data/all.jsonl` to match the canonical split order.
3. Run `python3 scripts/validate.py`.
4. Commit with a message describing what scenario is covered and why it was added.

## Notes

- Keep this repo dependency-free unless there is a strong reason not to.
- `scripts/convert-yaml-to-jsonl.ts` is optional and expects `GIVECARE_EVALS_DIR` or sibling `../gc-sms/packages/evals/src/datasets`.
- Keep scenarios anonymized and SMS-length; the value is in curation and rubrics, not raw source text.
