# gc-evals Vision

`gc-evals` is GiveCare's public, reusable dataset of caregiver AI gold cases and
assessment instrument records.

## Product promise

Small, legible records let outsiders inspect and reuse the behaviors GiveCare
cares about without private product context. This repo is a dataset, not a
runner or live service.

## Governing beliefs

- Public usefulness begins with strict privacy and anonymization.
- A gold case should be understandable without GiveCare context.
- Assessment instruments should ship only with clear redistribution rights.
- A verified failure is a candidate for human review, not automatic public
  data or product authority.
- Stable, inspectable records matter more than dataset size.

## Direction

The dataset should grow toward better caregiver-behavior coverage and clearer
outside reuse. Instrument distribution should remain faithful to its public
source while the gold cases stay independent of any one runner or model.

## Success

`gc-evals` succeeds when an outsider can inspect and reuse public caregiver AI
cases and instrument records without private prompts, traces, identities, or
product assumptions.

## Refusals

- A runner, verifier, scoring implementation, or live policy system.
- Private-trace ingestion or identifying detail.
- Benefits data or generated source corpora.
- Automatic promotion from a failure signal.

## Document boundary

Dataset boundaries live in [CODEMAP.md](CODEMAP.md). Operating detail lives in
[CLAUDE.md](CLAUDE.md) and [the Hound guide](docs/hound.md).
