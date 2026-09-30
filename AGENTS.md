# gc-evals Agent Rules

Type: reference.

This repo owns public eval records and instrument distribution. Root workspace
`AGENTS.md` rules apply; this file adds local gates. Read `VISION.md` before
non-trivial work.

## Authority

- Public eval records (`data/*.jsonl`) belong here. Scoring semantics belong to
  `gc-tools`, runners, adapters, and judge prompts to `gc-bench`, benefits data to
  `gc-benefits`, production runtime to `gc-sms`.
- `evals.gold-cases.apply` is the only gold-case authoring path. It is human-gated:
  a reviewer applies one verified, public-safe intake as an ordinary Git edit.
  There is no automated writer, and a reviewed gold case is only added, never deleted.
- `data/all.jsonl` is written only by `scripts/project_gold_cases.py`.
- `data/instruments.json` is written only by `scripts/sync_instruments.py` from one
  verified gc-tools projection at an exact owner commit
  (`evals.instruments.sync-owner-projection`).

## Required path

Follow [`docs/evidence.md`](docs/evidence.md) for every gold-case change. A
consumer reads `data/all.jsonl` only through a Git-addressed
`givecare.artifact-ref/v1` verified by the workspace `projection-ref` command.

## Proof

Before handoff run the unit tests and `scripts/validate.py --tools-commit <full-gc-tools-commit>`
(see `CLAUDE.md` § Commands). Report only checks that ran.

## Safety

- Contribute no private conversations, production traces, raw forum text, usernames,
  identifying links, unlicensed instruments, benefits catalogs, or private prompts
  and product internals ([`CONTRIBUTING.md`](CONTRIBUTING.md)).
- Do not present clinical, legal, or eligibility determinations as ground truth.
- Report private or unsafe content privately per [`SECURITY.md`](SECURITY.md); never
  in a public issue.
