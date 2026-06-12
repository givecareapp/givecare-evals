# Codemap

Generated: 2026-04-30

## Architecture

GiveCare Evals is a dependency-free dataset repo. The source of truth is JSON/JSONL under `data/`. There is no runtime package and no model adapter in this repo.

## Files

| Path | Purpose |
|------|---------|
| `data/core-behaviors.jsonl` | Functional behavior checks for caregiver-support assistants |
| `data/red-team.jsonl` | Prompt attacks and boundary violations |
| `data/reddit-caregivers.jsonl` | SMS-style caregiver scenarios adapted from public posts |
| `data/multi-turn.jsonl` | Cases requiring assumed context or continuity |
| `data/all.jsonl` | Canonical concatenation of the four eval splits |
| `data/instruments.json` | Public SDOH-6, EMA-3, and SDOH-30 instrument definitions |
| `scripts/validate.py` | Stdlib validation for dataset shape and split consistency |
| `scripts/convert-yaml-to-jsonl.ts` | Optional internal conversion helper for Promptfoo YAML sources |

## Data contract

Each JSONL record must include:

- `id`
- `split`
- `category`
- `subcategory`
- `input`
- `expected_behaviors`
- `forbidden_patterns`
- `context.prior_state` for `multi-turn` records

`data/all.jsonl` must equal this exact split order:

1. `core-behaviors.jsonl`
2. `red-team.jsonl`
3. `reddit-caregivers.jsonl`
4. `multi-turn.jsonl`

## Repo boundaries

| Concern | Owner |
|---------|-------|
| Public eval records | `givecare-evals` |
| Public SDOH scoring implementation | `givecare-tools` / `@givecare/tools` |
| Benchmark runner, model adapters, judge prompts | `gc-bench` |
| Benefits data | `gc-benefits` |
| Production runtime | `gc-sms` |
