# gc-evals

Pure JSONL eval dataset repo. No build step, no runtime — just versioned test cases published to HuggingFace.

## Repo

`givecareapp/caregiver-evals` — published to HuggingFace as `GiveCare Caregiver AI Evaluation Dataset` (CC-BY-4.0).

## What's here

```
data/
  all.jsonl              # merged dataset (all splits)
  core-behaviors.jsonl   # 40 functional tests
  red-team.jsonl         # 22 adversarial attacks
  reddit-caregivers.jsonl# 47 real caregiver scenarios (adapted Reddit posts)
  multi-turn.jsonl       # 9 stateful conversation scenarios
  benefits-programs.jsonl# 102 US caregiver benefit programs
  instruments.json       # 3 validated caregiver assessment instruments
scripts/
  convert-yaml-to-jsonl.ts  # YAML → JSONL conversion utility (needs node/tsx)
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
  "forbidden_behaviors": ["..."]
}
```

## How gc-bench uses this

`gc-bench` (`../gc-bench`) reads `data/*.jsonl` directly to drive benchmark runs. Both repos must be siblings for local dev paths to resolve.

## Adding eval cases

1. Add records to the appropriate `data/*.jsonl` file (one JSON object per line).
2. Update `data/all.jsonl` (rerun the merge script or append manually).
3. Commit with a message describing what scenario is covered and why it was added.

## No package.json / pyproject.toml

This repo is intentionally dependency-free. The `node_modules/` present is only for the `scripts/convert-yaml-to-jsonl.ts` utility (yaml parser). It is not a deployable package.
