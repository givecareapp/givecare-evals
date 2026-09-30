# Codemap

Type: reference.

GiveCare Evals is a dependency-free dataset repo. JSON/JSONL under `data/` is the
source of truth. No runtime service or model adapter lives here.

```text
data/
  core-behaviors.jsonl        functional behavior checks
  red-team.jsonl              prompt attacks and boundary violations
  reddit-caregivers.jsonl     SMS-style scenarios adapted from public posts
  multi-turn.jsonl            cases needing assumed context or continuity
  all.jsonl                   generated concatenation of the four splits
  instruments.json            exact materialization of the gc-tools projection
                              (owner file: gc-tools data/instruments-export.json)
  instruments-overlay.json    Evals-only public packaging fields
scripts/
  project_gold_cases.py       rebuilds data/all.jsonl and re-validates it
  validate.py                 stdlib validation of shape, splits, and parity
  sync_instruments.py         materializes one exact gc-tools projection
  read_instruments.py         public projection-plus-overlay reader
tests/                        unit tests for validation and projection
docs/evidence.md              gold-case intake and rebuild (how-to)
.github/workflows/ci.yml      runs the unit tests
.givecare/module.json         module declaration
README.md                     dataset card
VISION.md  ROADMAP.md         scope and known gaps
CONTRIBUTING.md  SECURITY.md  contributor and reporting rules
CITATION.cff  LICENSE         citation metadata, CC-BY-4.0
```

## Data contract

Every JSONL record has `id`, `split`, `category`, `subcategory`, `input`,
`expected_behaviors`, and `forbidden_patterns`; `multi-turn` records also carry
`context.prior_state`. `data/all.jsonl` is the four splits in the order
`core-behaviors`, `red-team`, `reddit-caregivers`, `multi-turn`. Each split stays
at or above its shipped baseline count; a reviewed gold case is only added.

Gold-case authoring and projection: [`docs/evidence.md`](docs/evidence.md).
