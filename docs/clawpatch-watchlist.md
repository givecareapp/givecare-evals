# Clawpatch Eval Dataset Watchlist

Use Clawpatch as a review ledger for public dataset integrity, not as an
automatic fixer. The goal is to catch public-safety, anonymization, split,
instrument-rights, and benchmark-staging mistakes that a schema validator may
not frame.

## Operating Rules

- Keep `.clawpatch/` local. Do not commit generated maps, findings, reports, or
  patch attempts.
- Review first. Do not run `clawpatch fix` until a human has triaged the
  finding and picked a scope.
- Do not add private prompts, traces, memory records, usernames, links, or raw
  public-post text.
- This repo is a public dataset, not a benchmark runner.

## Setup

```bash
clawpatch --version
clawpatch init
clawpatch map --source agent --reasoning-effort low
```

## Canonical Watchlist

| Watch item | Trigger it when changes touch | Ask Clawpatch to look for | Local verification anchors |
| --- | --- | --- | --- |
| Eval records | `data/*.jsonl`, `data/all.jsonl` | Duplicate IDs, wrong split, non-SMS-like input, identifying details, raw public-post text, expected behavior that belongs in benchmark scorer. | `python3 scripts/validate.py`. |
| Public instruments | `data/instruments.json`, SDOH/EMA docs | Redistribution uncertainty, scoring/spec drift from `gc-tools`, missing instrument ID, private adaptation notes. | `python3 scripts/validate.py`, compare `../gc-tools/GC-SDOH.md` when scoring semantics change. |
| Dataset packaging | `README.md`, `CITATION.cff`, `ROADMAP.md`, `CONTRIBUTING.md` | Claims beyond public dataset scope, stale split counts, confusing relationship to `gc-bench`. | `python3 scripts/validate.py`, README split table. |
| Optional converters | `scripts/convert-yaml-to-jsonl.ts`, `scripts/validate.py` | Private Promptfoo dependency assumptions, malformed merged order, validation holes. | `python3 scripts/validate.py`. |
| Cross-repo staging | Material intended for `../gc-bench` | Benchmark logic added here, private trace promotion, missing provenance for candidate scenarios. | Import through `gc-bench` staging tools, not direct runner code here. |

## Triage

Treat findings as review input. A finding is actionable only after the public
safety risk, dataset field, and validation command are clear.
