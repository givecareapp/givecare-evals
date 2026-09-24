# Codemap

Generated: 2026-08-06

## Architecture

GiveCare Evals is a dependency-free dataset repo. The source of truth is JSON/JSONL under `data/`. A human-reviewed Git edit is the owner-local change path; `scripts/project_gold_cases.py` is the plain owner projection script. There is no runtime service or model adapter in this repo.

## Files

| Path | Purpose |
|------|---------|
| `data/core-behaviors.jsonl` | Functional behavior checks for caregiver-support assistants |
| `data/red-team.jsonl` | Prompt attacks and boundary violations |
| `data/reddit-caregivers.jsonl` | SMS-style caregiver scenarios adapted from public posts |
| `data/multi-turn.jsonl` | Cases requiring assumed context or continuity |
| `data/all.jsonl` | Canonical concatenation of the four eval splits |
| `data/instruments.json` | Exact verified materialization of the Tools projection |
| `data/instruments-overlay.json` | Evals-only public packaging fields |
| `scripts/project_gold_cases.py` | Rebuilds `data/all.jsonl` from the splits and re-validates it |
| `scripts/validate.py` | Stdlib validation for dataset shape and split consistency |
| `scripts/sync_instruments.py` | Exact Tools projection materializer |
| `scripts/read_instruments.py` | Public projection-plus-overlay reader |

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

Each split must stay at or above its shipped baseline count. A reviewed gold
case is only ever added; there is no delete operation.

`evals.gold-cases.apply` is the only supported gold-case authoring path. There
is no automated adapter for it: a reviewer binds a verified failure artifact,
release checks, and one gold case to the shared root Trace validator, then
appends the record to the selected source split by hand.
The shared root Trace validator resolves historical module pins before the
reviewer checks the `evals.dataset` target.

Run `python3 scripts/project_gold_cases.py` after each apply. It alone
rebuilds `data/all.jsonl`; a consumer verifies its `givecare.artifact-ref/v1`
through the workspace `projection-ref` command before import.

Instrument sync consumes only one explicit verified gc-tools `methods.assessment.project`
projection at an exact owner commit. That commit must carry the exact public
ArtifactRef and digest for `data/instruments-export.json`. The sync writes
those exact bytes to the fixed `data/instruments.json` path. The validator
rejects byte drift and overlay attempts to shadow owner fields. The module
capability is `evals.instruments.sync-owner-projection`.

## Repo boundaries

| Concern | Owner |
|---------|-------|
| Public eval records | `givecare-evals` |
| Public SDOH scoring implementation | `givecare-tools` / `@givecare/tools` |
| Benchmark runner, model adapters, judge prompts | `gc-bench` |
| Benefits data | `gc-benefits` |
| Production runtime | `gc-sms` |
