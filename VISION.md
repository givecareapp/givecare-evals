# givecare-evals Vision

`givecare-evals` is GiveCare's public caregiver AI eval dataset: versioned,
anonymized, SMS-style evaluation records plus public GiveCare SDOH instruments
that can be distributed without exposing private runtime data.

This document is the repo's product and agent decision frame. It explains where
the dataset is going, what matters now, and which changes are out of bounds. For
ownership and evaluation contracts, see `CHARTER.md`.

## The Product Bet

`givecare-evals` makes GiveCare's evaluation posture inspectable and reusable. It
lets external researchers, partners, and standards efforts test caregiver AI
behavior using the same kinds of cases GiveCare cares about — while keeping the
dataset public, small, anonymized, legally safe, and clearly separated from
private production traces.

It is data distribution, not a benchmark runner and not the product runtime. The
value is portability: an outsider should be able to understand and reuse a case
without any private GiveCare context.

## Current Focus

Priority:

- Public-safe, anonymized, SMS-like cases with no private prompts, traces, or
  identifying details.
- Split integrity: validated split counts, unique IDs, required fields, and
  merged dataset order.
- Public SDOH-6, EMA-3, and SDOH-30 instrument records with clear redistribution
  rights.

Next priorities:

- Candidate scenario material that flows cleanly into `../gc-bench` staging.
- Coverage of meaningful caregiver AI behaviors surfaced by `../gc-bench`,
  `../gc-sms`, and public research.
- Packaging discipline for GitHub / Hugging Face style distribution.

## Public-Safety Rule

No private production prompts, traces, memory records, or user conversations.
Inputs stay short, anonymized, SMS-like, and public-safe. Instruments ship only
where redistribution rights are clear. Benefits data does not belong here.

## Repo Boundary

`givecare-evals` owns the public JSONL eval records, split definitions and
validation, the public instrument records, and anonymization discipline. It does
not own executable runners/verifiers/scoring (that is `../gc-bench`), live SMS
behavior (`../gc-sms`), benefits records (`../gc-benefits`), or TypeScript
scoring implementation (`../givecare-tools`). Full ownership matrix is in
`CHARTER.md`.

## Source Of Truth

- Public eval cases and instrument records are canonical here.
- Executable benchmark behavior is canonical in `../gc-bench`.
- Scoring implementation is canonical in `../givecare-tools`.
- Private runtime behavior is canonical in `../gc-sms`.

## Evaluation Loop

Every case should add a caregiver AI behavior signal not better owned elsewhere,
stay public-safe and anonymized, and preserve dataset format and split integrity.
Run `python scripts/validate.py` before considering a change done.

## Agent Rules

- Never add raw public-post text, usernames, links, private messages, or
  identifying details.
- Never add private traces because they are useful — route those to the safe
  harvest/review path in `../gc-bench`.
- Keep this repo a dataset, not a runner or scorer.
- Do not reintroduce benefits programs or generated source data.
- Ship instruments only with clear redistribution rights.

## What Not To Build For Now

- A benchmark runner or scorer implementation here.
- Private-trace ingestion outside the anonymized, reviewed path.
- Benefits or generated source data.
- Instruments with uncertain redistribution rights.

## Read Order

- `VISION.md` → dataset direction, priority frame, and agent guardrails.
- `CHARTER.md` → ownership and evaluation contract.
- `CLAUDE.md` → dataset structure, splits, and SDOH instruments.
- `../VISION.md` → ecosystem direction and cross-repo seams.
