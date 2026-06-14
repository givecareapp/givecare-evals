# givecare-evals Charter

This charter is an evaluation document, not an operating manual. For the shared
GiveCare North Star, see `~/agents/wiki/givecare/givecare-system.md`.

## Purpose

`givecare-evals` is the public caregiver AI eval dataset repo. It contains
versioned, anonymized, SMS-style evaluation records and public GiveCare SDOH
instruments that can be distributed without exposing private runtime data.

## Role In GiveCare

`givecare-evals` belongs to the evaluation layer and open-source credibility
domain. It supplies portable eval cases and instruments that can seed
benchmarking, external research, and standards work. It is data distribution,
not the benchmark runner and not the product runtime.

## Product / System Promise

The repo should make GiveCare's evaluation posture inspectable and reusable. It
should help others test caregiver AI behavior while keeping the dataset public,
small, anonymized, legally safe, and clearly separated from private production
traces.

## What This Repo Owns

- Public JSONL caregiver AI safety and quality eval records.
- Dataset split definitions and validation.
- Public SDOH-6, EMA-3, and SDOH-30 instrument records.
- Anonymization, public-safety boundaries, and dataset packaging discipline.
- Candidate eval material that may be imported into `../gc-bench` staging.

## What This Repo Does Not Own

- Executable benchmark runners, model adapters, verifier prompts, scoring, scans,
  and leaderboard artifacts. Those belong in `../gc-bench`.
- Live SMS behavior, prompts, memory, Convex state, or private traces. Those
  belong in `../gc-sms`.
- Benefits program records. Those belong in `../gc-benefits`.
- TypeScript scoring implementation and SDK packaging. Those belong in
  `../givecare-tools`.
- Copyrighted or restricted instruments unless redistribution rights are clear.

## Inputs

- Public-safe caregiver scenarios, red-team cases, adapted public examples, and
  multi-turn evaluation ideas.
- Public GiveCare assessment-instrument definitions.
- Gaps discovered by `../gc-bench`, `../gc-sms`, public research, or partner-safe
  analysis.

## Outputs

- `data/*.jsonl` eval splits and merged `data/all.jsonl`.
- `data/instruments.json`.
- Validated public dataset artifacts for GitHub/Hugging Face style distribution.
- Candidate scenario material that can flow into `../gc-bench`.

## Core Invariants

- No private production prompts, traces, memory records, or user conversations.
- Inputs must be short, anonymized, SMS-like, and public-safe.
- Split counts, duplicate IDs, required fields, and merged dataset order must
  validate.
- Benefits data must not be reintroduced here.
- Dataset scope should remain portable and understandable without the GiveCare
  runtime.

## Evaluation Questions

- Does this case add a meaningful caregiver AI behavior signal that is not better
  owned by `../gc-bench` or `../gc-sms`?
- Is the record public-safe, anonymized, and free of private or identifying
  details?
- Does it preserve dataset format, split integrity, and validation?
- Could an external researcher understand and reuse the case without private
  GiveCare context?
- Does it improve the path from eval dataset to benchmark staging and product
  learning?

## Anti-Patterns

- Adding raw public-post text, usernames, links, private messages, or identifying
  details.
- Treating this repo as a benchmark runner or scorer implementation.
- Adding private traces because they are useful.
- Adding benefits programs or generated source data.
- Shipping instruments where redistribution rights are uncertain.

## Related Documents

- `CLAUDE.md`
- `scripts/validate.py`
- `../gc-bench/CHARTER.md`
- `../givecare-tools/CHARTER.md`
- `~/agents/wiki/givecare/givecare-system.md`
