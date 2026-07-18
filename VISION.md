# gc-evals Vision

`gc-evals` distributes public, anonymized caregiver AI cases and assessment
instrument records.

## Product bet

Small, legible records let outsiders inspect and reuse the behaviors GiveCare
cares about without private product context. This repo is a dataset, not a
runner or live service.

## Ownership

This repo owns public JSONL cases, splits, validation, instrument records, and
anonymization. `gc-bench` owns executable evaluation; `gc-tools` owns scoring
code; `gc-sms` owns runtime behavior; `gc-benefits` owns program facts.

## Invariants

- No private prompts, traces, conversations, usernames, links, or identifying
  details.
- Inputs remain short, SMS-like, and understandable without GiveCare context.
- Instruments ship only with clear redistribution rights.
- IDs, fields, split counts, and merged order pass `scripts/validate.py`.

## Current focus

- Public-safe cases with useful caregiver-behavior coverage.
- GC-SDOH-6, EMA-3, and GC-SDOH-30 distribution records.
- Clean candidate flow into `gc-bench` staging.

## Non-goals

- A runner, verifier, or scoring implementation.
- Private-trace ingestion.
- Benefits data or generated source corpora.
