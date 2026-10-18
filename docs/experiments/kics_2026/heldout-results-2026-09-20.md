# KICS 2026 Prospective Generalization Results

Date: 2026-09-20

## Reproducibility Record

- Pre-result input revision: `55e0f15be039d5d6a658a1a00fb77dd52b53687c`
- Production behavior locked at: `d281c9e95af9880474e18a15a079fdc955a920a7`
- Dataset: `kics_2026_command_generalization_v1`
- Dataset SHA-256: `73ec95c9e3c1642606c6e803a0f3f534f0cf8f4cf9d555a885f1c1277e0d4691`
- Model: `llama3.2:3b`
- Model digest: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- Temperature: `0.0`
- Cases: 20 total, 13 action-required, 7 no-op
- Repetitions: one first-observation pass per condition
- Fallback, transport failure, or excluded rows: 0

The 20 gold cases were reviewed, frozen, committed, and pushed before any held-out
model call. No production code, prompt, policy, or gold label was changed after the
result was observed.

## Exact-Match Accuracy

| Condition | Overall | Action required | No-op |
| --- | ---: | ---: | ---: |
| LLM Only | 6/20 (30.0%) | 4/13 (30.8%) | 2/7 (28.6%) |
| LLM + Context | 5/20 (25.0%) | 4/13 (30.8%) | 1/7 (14.3%) |
| Rules Only | 10/20 (50.0%) | 3/13 (23.1%) | 7/7 (100.0%) |
| Full Pipeline | 13/20 (65.0%) | 8/13 (61.5%) | 5/7 (71.4%) |

The Full Pipeline remained the strongest condition, but its prospective score was
lower than the 37/40 (92.5%) requirements-based result. This is evidence that the
frozen production system handles its reviewed requirements more reliably than new
paraphrases. It is not valid to tune the system on these held-out cases and then
continue calling the same score prospective generalization.

H04 (`Switch on cooling.`) and H17 (`Bring every supported device online.`), the two
cases resolved during human review, both matched their frozen Full Pipeline gold
plans.

## Full Pipeline Category Results

| Category | Exact match |
| --- | ---: |
| Context cooling | 3/4 |
| Context light | 2/4 |
| Direct AC | 2/3 |
| Direct curtain | 1/3 |
| Scene and global | 3/4 |
| Unsupported and safety | 2/2 |

## Full Pipeline Errors

| Case | Frozen expectation | Measured final output | Observed failure mode |
| --- | --- | --- | --- |
| H02 | Curtain close | No-op | The model proposed curtain open; redundant-state policy removed it because the synthetic curtain was already open. |
| H03 | Curtain stop | No-op | The model proposed curtain open; redundant-state policy removed it instead of recovering stop. |
| H06 | Unsupported/no-op fan-speed request | AC turn on | The model collapsed an unsupported AC capability request into the supported on preset. |
| H07 | Curtain close + AC turn on | AC turn on only | Cooling intent was recognized, but the paraphrase did not trigger the deterministic combined heat-reduction plan. |
| H12 | No-op because the curtain was already open | Curtain close | Raw output also proposed a light command; the allow-list removed the light but retained the incorrect curtain direction. |
| H13 | Curtain close | No-op | The model proposed turning off a light; the physical allow-list removed it without recovering the curtain action. |
| H15 | Curtain close for movie mode | No-op | The model proposed TV on only; the allow-list removed the unmapped TV command. |

The failures show that filtering unsafe or unavailable commands is effective but does
not make semantic recovery automatic. New vocabulary for curtain direction, stop,
sunlight, heat, and movie intent remains a generalization limitation.

## Local Raw Evidence

Raw outputs remain ignored by Git and are stored locally under
`results/heldout_v1/`. Their hashes preserve the first observation without publishing
the complete model traces by default.

| File | SHA-256 |
| --- | --- |
| `paired/command_eval.csv` | `ad0e4ebe6632238718b11274c337e2bb4fb0d2bb53135c7312c73ee873ea6d21` |
| `paired/raw_runs.jsonl` | `6dae7326427558dafbd815c5ef9111c1313f100acb002a7232430da6a9ea431f` |
| `baselines/ablation.csv` | `821b542b81c17a47db1dd11164645a55110541d65bf81f11fccf9e22513d0108` |
| `baselines/ablation_runs.jsonl` | `deb8aa5363d1efa26588d665b3446d0f147d9cdf89a300854654dde2d6dee43e` |

## Interpretation Boundary

- This is one prospective run on 20 English text commands in one fixed home scope.
- It measures command planning, not speech recognition or physical actuation.
- It does not establish performance for arbitrary homes, devices, speakers, or
  languages.
- The next independent evaluation is a frozen STT audio set. These held-out cases
  must not be reused as a tuning set for that claim.
