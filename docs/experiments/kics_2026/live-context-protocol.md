# KICS 2026 Live Context and Safety Protocol

Date frozen: 2026-09-25

## Purpose

This protocol tests the deployed controller against a fresh physical Home Assistant
context rather than a synthetic evaluation fixture. It separates two claims:

- a context threshold can authorize a curtain action; and
- the same request is suppressed when the required action is redundant or unsafe.

## Frozen Cases

`live_context_cases.json` contains six pre-result cases.

| Case | Live precondition | Request | Expected outcome |
| --- | --- | --- | --- |
| L01 | illuminance >= 800 lux; curtain open | `It's too bright in here.` | close curtain |
| L02 | illuminance >= 800 lux; curtain closed | same | no action |
| L03 | illuminance <= 100 lux; curtain closed | `It's dark in here.` | open curtain |
| L04 | illuminance <= 100 lux; curtain open | same | no action |
| L05 | none | unsupported AC fan-speed request | no action |
| L06 | none | undefined scene request | no action |

The thresholds are the deployed `is_bright` and `is_dark` policy thresholds. A live
reading is sampled before every request; the runner does not manipulate a sensor or
repair a failed curtain precondition.

## Measured Path

```text
text request -> current Home Assistant context -> local LLM and normalization
-> policy and physical allow-list -> Home Assistant -> Matter bridge -> curtain
```

For an action case, success requires the frozen parsed intent and command plus the
expected final Home Assistant cover state. For a no-action case, success requires an
empty final command list, no applied service calls, and any declared curtain state to
remain unchanged. These checks do not claim camera-observed physical completion.

## Execution

The dataset must be committed before its first execution. Start the deployed physical
backend, then run a new output directory for each run:

```bash
.venv/bin/python docs/experiments/kics_2026/run_live_context_e2e.py \
  --allow-actuation --case L01 --case L02 \
  --output-dir docs/experiments/kics_2026/results/live_context_v1/bright_run1
```

Run L03 and L04 only after an operator has safely reduced the live sensor reading to
the frozen dark precondition. Raw JSONL remains ignored by Git; reviewed summaries
record hashes, eligible counts, and interpretation limits.
