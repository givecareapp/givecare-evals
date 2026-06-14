# givecare-evals

> Ecosystem context: see `~/agents/wiki/givecare/givecare-system.md` — this repo is in the **evaluation layer + open-source credibility** domain.
>
> Direction: see `VISION.md` — product bet, current focus, and agent guardrails. `CHARTER.md` owns the ownership and evaluation contract.

Pure public dataset repo. No runtime package. No private traces. It contains versioned caregiver AI eval records and public SDOH instruments, intended for GitHub and Hugging Face distribution.

## Repo

`givecareapp/givecare-evals` — public caregiver AI safety eval dataset (CC-BY-4.0).

## Scope

Included:

- Caregiver AI safety and quality eval cases
- Red-team and boundary scenarios
- Adapted public caregiver scenarios rewritten into SMS-style messages
- Multi-turn continuity scenarios
- Public GiveCare SDOH instruments: SDOH-6, EMA-3, SDOH-30

Excluded:

- Benefits program catalog (canonical owner: `../gc-benefits`)
- Private runtime, prompts, traces, memory, and user data
- Production benchmark runner and scoring harness (canonical owner: `../gc-bench`)
- CWBS-14 redistribution material pending original-author licensing confirmation

## What's here

```text
data/
  all.jsonl               # merged dataset (all eval splits)
  core-behaviors.jsonl    # 40 functional tests
  red-team.jsonl          # 22 adversarial attacks
  reddit-caregivers.jsonl # 47 realistic caregiver scenarios adapted from public posts
  multi-turn.jsonl        # 9 stateful conversation scenarios
  instruments.json        # 3 public caregiver SDOH assessment instruments
scripts/
  convert-yaml-to-jsonl.ts # optional YAML -> JSONL conversion utility
  validate.py              # dependency-free dataset validator
```

## Record format

```jsonc
{
  "id": "reddit-caregivers-007",
  "split": "reddit-caregivers",
  "category": "crisis-adjacent",
  "subcategory": "...",
  "input": "caregiver message text",
  "expected_behaviors": ["..."],
  "forbidden_patterns": ["..."],
  "context": {"prior_state": ["Required for multi-turn rows."]}
}
```

## Validation

```bash
python3 scripts/validate.py
```

Checks:

- split counts: 40/22/47/9
- required fields and duplicate IDs
- high-risk safety rows include `expected_behaviors`
- SMS-format rows include a positive length/shape rubric
- forbidden patterns avoid overbroad single-word literals
- multi-turn rows include `context.prior_state`
- `data/all.jsonl` exactly equals canonical split concatenation
- `data/instruments.json` contains only `sdoh6`, `ema3`, `sdoh30`
- `data/instruments.json` documents inverted GiveCare Score semantics
- adapted Reddit inputs do not reintroduce links, usernames, known personal names,
  or high-specificity source markers
- stale `data/benefits-programs.jsonl` has not been reintroduced

## Clawpatch Review

Use `docs/clawpatch-watchlist.md` for public-dataset review passes. The repo
config is `clawpatch.config.json`; generated `.clawpatch/` state stays local and
ignored. Do not use Clawpatch as an automatic fixer, and keep private traces,
raw public-post text, usernames, links, and identifying details out of the
dataset.

## Relationship to other repos

- `../gc-bench` owns executable benchmark runners, model adapters, scoring, and reports.
- Private/source Promptfoo YAMLs are not an active dependency; set `GIVECARE_EVALS_DIR` explicitly when using the optional converter.
- `../gc-benefits` owns benefits data. Do not add benefits records here.
- `../gc-tools` / public `givecare-tools` owns the TypeScript SDOH instrument/scoring implementation.

## Updating eval cases

1. Edit the appropriate split file in `data/*.jsonl`.
2. Update `data/all.jsonl` to match canonical split order.
3. Run `python3 scripts/validate.py`.
4. Commit with a message describing the scenario and why it belongs in the public eval set.

## Open-source rules

- Keep inputs short, anonymized, and SMS-like.
- Do not add raw Reddit text, usernames, links, private messages, or identifying details.
- Do not add private production prompts, traces, memory records, or user conversations.
- Do not add copyrighted instruments unless redistribution rights are explicit.
- Do not re-add benefits program data; use `gc-benefits` for that pipeline.
