# AGENTS.md — gc-evals

Type: reference.

This repo owns public eval records and instrument distribution. Root workspace
`AGENTS.md` rules apply; this file adds local gates. Owner intent:
`/home/deploy/wiki/aims/givecare-instruments.md`.

## Layout

- `data/`: JSONL splits `core-behaviors`, `red-team`, `reddit-caregivers`,
  `multi-turn`; generated `all.jsonl` (their concatenation, in that order);
  `instruments.json` (byte copy of the gc-tools projection) and
  `instruments-overlay.json` (Evals-only public packaging fields).
- `scripts/`: `validate.py`, `project_gold_cases.py`, `sync_instruments.py`,
  `read_instruments.py` (public projection-plus-overlay reader).
- `tests/`: unit tests. `docs/evidence.md`: gold-case intake and rebuild (how-to).
- `README.md` dataset card; `ROADMAP.md`; `CONTRIBUTING.md`; `SECURITY.md`;
  `.givecare/module.json`.

Every JSONL record has `id`, `split`, `category`, `subcategory`, `input`,
`expected_behaviors`, `forbidden_patterns`; `multi-turn` also carries
`context.prior_state`. Inputs are anonymized and usable without private context.

## Commands

```bash
python3 -m unittest discover -s tests
python3 scripts/validate.py --tools-commit <full-gc-tools-commit>
python3 scripts/project_gold_cases.py     # rebuild data/all.jsonl
python3 scripts/sync_instruments.py --owner-commit <full-gc-tools-commit>
```

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

Follow [`docs/evidence.md`](docs/evidence.md) for every gold-case change. Each split stays at or above its shipped baseline count. A
consumer reads `data/all.jsonl` only through a Git-addressed
`givecare.artifact-ref/v1` verified by the workspace `projection-ref` command.

## Proof

Before handoff run the unit tests and `scripts/validate.py --tools-commit <full-gc-tools-commit>`
(see Commands). Report only checks that ran.

## Safety

- Contribute no private conversations, production traces, raw forum text, usernames,
  identifying links, unlicensed instruments (licensing wall: `gc-tools/AGENTS.md` § Safety; CWBS-14 content is excluded, redistribution unconfirmed), benefits catalogs, or private prompts
  and product internals ([`CONTRIBUTING.md`](CONTRIBUTING.md)).
- No runner, verifier, scoring implementation, or live policy system here. A
  failure signal never promotes itself into public data.
- Do not present clinical, legal, or eligibility determinations as ground truth.
- Report private or unsafe content privately per [`SECURITY.md`](SECURITY.md); never
  in a public issue.

## Gotchas

- `data/all.jsonl` is generated; never hand-edit it.
- `data/instruments.json` is a byte copy of the Tools projection, not an Evals edit;
  the validator rejects drift.
- `--tools-commit` must be a full commit reachable in the sibling `gc-tools`.

## Pointers

- `docs/evidence.md`: gold-case intake and rebuild.
- `gc-bench` imports the owner projection as candidates and owns execution and
  verdicts. `gc-tools` owns executable scoring semantics.
