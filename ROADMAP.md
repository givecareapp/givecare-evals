<!-- Diátaxis: explanation -->

# Roadmap and known gaps

GiveCare Evals is useful today as a small public dataset. It is not yet a complete benchmark package.

## Biggest gaps

1. **Executable harness**
   - Current state: JSONL data and natural-language rubrics.
   - Gap: no CLI, model adapter, judge prompt, scoring script, or report format in this repo.

2. **Machine-readable judge schema**
   - Current state: `expected_behaviors` and `forbidden_patterns` are readable by humans and LLM judges.
   - Gap: criteria do not yet have severity, scoring weights, pass/fail IDs, or per-case safety category labels.

3. **Baseline results**
   - Current state: no checked-in model scorecards.
   - Gap: users cannot compare their results against public reference runs.

4. **Provenance granularity**
   - Current state: adapted caregiver scenarios are anonymized and grouped by source family.
   - Gap: no per-case public source URL is retained. This protects privacy but limits reproducibility.

5. **Coverage**
   - Current state: 118 English, SMS-style cases.
   - Gap: limited language, geography, channel, disability, cultural, and care-setting coverage.

6. **Release automation**
   - Current state: GitHub CI validates the files.
   - Gap: no automated Hugging Face publish, versioned dataset card release, or changelog workflow.

## Near-term improvements

- Add a small Python runner that can call a model function and emit JSONL responses.
- Split `expected_behaviors` into structured criteria with IDs and severity.
- Add `severity`, `risk_area`, and `judge_notes` fields without breaking existing rows.
- Publish reference baseline runs for at least one open model and one frontier model.
- Add more cases for non-dementia caregiving, pediatric caregiving, disability caregiving, rural access, and non-US contexts.
