# KICS 2026 Five-Run Stability Results

Date: 2026-09-20

## Experiment Identity

- Frozen system input revision: `d281c9e95af9880474e18a15a079fdc955a920a7`
- Stability tooling revision: `6a09feac1c19de7aa480b548f9eaa93669b378ee`
- Dataset SHA-256: `80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`
- Model: `llama3.2:3b`
- Model digest: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- Temperature: `0.0`
- Repetitions: five complete 40-case runs per condition
- Total normalized condition rows: 800
- Fallback rows: 0
- Excluded rows: 0

Production code, prompt, model, dataset, contexts, and gold labels were not changed
between the initial measurement and this stability run. The tooling revision adds only
repeat-result validation and aggregation.

## Stability Result

| Condition | Overall mean +/- SD | Action mean +/- SD | No-op mean +/- SD | Always success | Variable | Always failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLM Only | 20.0 +/- 0.0% | 22.7 +/- 0.0% | 16.7 +/- 0.0% | 8 | 0 | 32 |
| LLM + Context | 20.0 +/- 0.0% | 27.3 +/- 0.0% | 11.1 +/- 0.0% | 8 | 0 | 32 |
| Rules Only | 77.5 +/- 0.0% | 59.1 +/- 0.0% | 100.0 +/- 0.0% | 31 | 0 | 9 |
| Full Pipeline | 92.5 +/- 0.0% | 90.9 +/- 0.0% | 94.4 +/- 0.0% | 37 | 0 | 3 |

Every condition reproduced the same case-level success and failure pattern in all five
runs. This shows deterministic repeatability under the fixed local runtime,
temperature-zero sampling, prompt, model digest, and input order. It does not establish
generalization to unseen commands, speakers, devices, or environments.

## Full Pipeline Case Stability

- Always successful: 37 cases, each 5/5.
- Variable: none.
- Always failed: C03, C09, and C34, each 0/5.
- Schema failures: none.
- Fallback or transport failures: none.

The three failures are the same failures documented in the initial run: an unseen
curtain-stop paraphrase, a semantically correct AC command with a non-canonical value,
and an invented bedtime scene. No code or gold label was changed in response.

## Paired Comparison

LLM + Context and Full Pipeline were scored from the same model inference in every
case. Each run produced 8/40 raw exact matches and 37/40 final exact matches. This
paired design isolates the effect of deterministic normalization, context policy,
schema validation, and physical allow-list enforcement from inference-to-inference
variation.

Rules Only remained correct for all 18 no-op cases but failed nine action-required or
scene cases. Full Pipeline recovered C01, C07, C08, and C29-C32 while losing C34,
giving a net improvement of six cases over Rules Only.

## Local Evidence Hashes

| File | SHA-256 |
| --- | --- |
| `paired/raw_runs.jsonl` | `d18b9f09aad5afdb662aaa20e76e9be4f581690d6430bd1e5b4171330633d351` |
| `paired/command_eval.csv` | `1bc90bcb63766a5a545df96eb90c5fa77065c4cd8d26e746f580dde17a808d2a` |
| `baselines/ablation_runs.jsonl` | `f159af862970bec9d56e75ad9191bb5a381e9c2d2db408d070beec893610caf5` |
| `baselines/ablation.csv` | `474f7a01c20899caad9e01e1df3092ff538f99751c9c6b20f67e7b7033b4da98` |
| `stability-summary.md` | `00686a7069ed7403c81624828fc813b5c44815346dd5f67c8956262bb5e53c89` |
| `case-success-counts.csv` | `a8e43f2d3a3e62da6388d482c8109bf80bf8ea3d34d6aac6e820a019183cd633` |

Raw files remain local and ignored by Git. This reviewed aggregate is the tracked
evidence used for reporting.

## Interpretation Boundary

The original 40 cases are a requirements-based frozen evaluation set, not a fully
independent unseen test set. Some policies were finalized during pre-freeze review.
The next generalization check must therefore use a prospective set that is reviewed
and frozen without changing production code before its first model execution.
