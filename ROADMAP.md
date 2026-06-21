<!-- Diátaxis: explanation -->

# Roadmap and known gaps

GiveCare Evals is useful today as a small public dataset. It is not a benchmark
runner: executable harnesses, model adapters, judge prompts, scoring scripts,
baseline scorecards, and benchmark reports belong in `../gc-bench`.

## Biggest gaps

1. **Structured criteria**
   - Current state: JSONL data and natural-language rubrics.
   - Gap: criteria do not yet have severity, scoring weights, pass/fail IDs, or
     per-case safety category labels.

2. **Benchmark handoff**
   - Current state: `../gc-bench` owns runners, model adapters, judge prompts,
     scoring, reports, and baseline scorecards.
   - Gap: this repo should document clean handoff expectations for candidate
     scenario material without adding executable benchmark logic here.

3. **Provenance granularity**
   - Current state: adapted caregiver scenarios are anonymized and grouped by source family.
   - Gap: no per-case public source URL is retained. This protects privacy but limits reproducibility.

4. **Coverage**
   - Current state: 118 English, SMS-style cases.
   - Gap: limited language, geography, channel, disability, cultural, and care-setting coverage.

5. **Distribution notes**
   - Current state: GitHub CI validates the files.
   - Gap: Hugging Face dataset-card updates, versioned distribution notes, and
     changelog expectations are still manual.

## Near-term improvements

- Split `expected_behaviors` into structured criteria with IDs and severity.
- Add `severity`, `risk_area`, and `judge_notes` fields without breaking existing rows.
- Document the `gc-evals` -> `gc-bench` handoff for candidate scenarios,
  including where benchmark runners, scoring, baselines, and reports live.
- Tighten GitHub / Hugging Face packaging notes for owner-controlled
  distribution.
- Add more cases for non-dementia caregiving, pediatric caregiving, disability caregiving, rural access, and non-US contexts.
