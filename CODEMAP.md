# Codemap

Generated: 2026-08-06

## Architecture

GiveCare Evals is a dependency-free dataset repo. The source of truth is JSON/JSONL under `data/`. Hound is the owner-local change kernel. There is no runtime service or model adapter in this repo.

## Files

| Path | Purpose |
|------|---------|
| `data/core-behaviors.jsonl` | Functional behavior checks for caregiver-support assistants |
| `data/red-team.jsonl` | Prompt attacks and boundary violations |
| `data/reddit-caregivers.jsonl` | SMS-style caregiver scenarios adapted from public posts |
| `data/multi-turn.jsonl` | Cases requiring assumed context or continuity |
| `data/all.jsonl` | Canonical concatenation of the four eval splits |
| `data/instruments.json` | Exact Hound-verified materialization of the Tools projection |
| `data/instruments-overlay.json` | Evals-only public packaging fields |
| `hound-driver.json` | Hound capabilities, human gate, and exact write scope |
| `scripts/hound_driver.py` | Strict intake and deterministic projection adapter |
| `scripts/validate.py` | Stdlib validation for dataset shape and split consistency |
| `scripts/sync_instruments.py` | Exact Tools projection materializer |
| `scripts/read_instruments.py` | Public projection-plus-overlay reader |
| `tests/test_hound_driver.py` | Intake, projection, and protocol proof |

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

Each split must stay at or above its shipped baseline count. Hound intake only
adds a reviewed gold case; it does not expose a delete operation.

`corpus.apply` is the only supported gold-case authoring path. It binds a
verified failure artifact, release checks, one gold case, the exact file
effect, and the next projection digest into one Hound plan. It writes only the
selected source split.
The shared root Trace validator resolves historical module pins before the
owner adapter checks the `evals.dataset` target.

Run `corpus.project` after each apply. It alone rebuilds `data/all.jsonl` and emits a
`givecare.artifact-ref/v1` that a consumer can verify before import.

Instrument sync consumes only one explicit verified gc-tools Hound
`corpus.project` run. The run must emit the exact public ArtifactRef and digest
for `data/instruments-export.json`. The sync writes those exact bytes to the
fixed `data/instruments.json` path. The validator rejects byte drift and
overlay attempts to shadow owner fields. The module capability is
`evals.instruments.sync-owner-projection`.

## Repo boundaries

| Concern | Owner |
|---------|-------|
| Public eval records | `givecare-evals` |
| Public SDOH scoring implementation | `givecare-tools` / `@givecare/tools` |
| Benchmark runner, model adapters, judge prompts | `gc-bench` |
| Benefits data | `gc-benefits` |
| Production runtime | `gc-sms` |
