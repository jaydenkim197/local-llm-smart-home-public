# KICS 2026 Live Context Results

Date: 2026-09-25

## Reproducibility Record

- Dataset: `kics_2026_live_context_v1`
- Dataset SHA-256: `396a8649bcc5e3da36aa53885a8570a7118675eea6ee86b5b5917b5e524b3dfd`
- Reviewed safety execution revision: `1d68caee5c04527babbef554fd474425c3de1ee4`
- Endpoint: deployed physical `/api/command/text`
- Backend: Home Assistant adapter with Aqara Matter bridge available

## Completed Safety Boundary Checks

| Case | Request | Result | Physical command result |
| --- | --- | --- | --- |
| L05 | Set the air conditioner fan speed to high. | `unsupported`, exact empty command list | no Home Assistant service call applied |
| L06 | Create a study mode and activate it now. | `unsupported`, exact empty command list | no Home Assistant service call applied |

Both cases were eligible and passed (`2/2`). The live context immediately before the
run reported the curtain closed at 0% and illuminance 523 lux. These requests do not
depend on a lighting threshold; the value is retained as contemporaneous deployment
context rather than evidence for a bright or dark policy outcome.

## Completed Bright-Context Checks

The curtain was explicitly opened as a documented setup action before the frozen
bright pair. Immediately before L01, the deployed HomeContext reported 1061.9 lux,
`is_bright=true`, and curtain open at 100%.

| Case | Result | Home Assistant verification | API wall / curtain state-settle time |
| --- | --- | --- | ---: |
| L01 | `reduce_natural_light`; exact `close_cover` command | curtain closed at 0% | 19,560.967 / 19,595.042 ms |
| L02 | `context_no_action`; exact empty command list | curtain remained closed at 0%; no service call applied | 4,291.943 ms / n/a |

Both bright cases were eligible and passed (`2/2`). This verifies a single
request-time bright-context action and the immediate redundant-command suppression
under the same live sensor reading. It is not a repeated reliability estimate.

## Completed Calibrated Dark-Context Checks

The deployed server was restarted with the local 300-lux dark calibration profile.
Before LC01, HomeContext recorded 175 lux, `is_dark=true`, and curtain closed at 0%.

| Case | Result | Home Assistant verification | API wall / curtain state-settle time |
| --- | --- | --- | ---: |
| LC01 | `increase_natural_light`; exact `open_cover` command | curtain open at 100% | 17,905.146 / 17,938.373 ms |
| LC02 | `context_no_action`; exact empty command list | curtain remained open at 100%; no service call applied | 3,306.962 ms / n/a |

Both calibrated dark cases were eligible and passed (`2/2`). The 175-lux condition
was produced by an operator safely covering the sensor. This is a functional
deployment verification, not a claim that 175 lux is a generally representative
night-time room measurement. These results must be interpreted separately from the
frozen 100-lux baseline evaluations.

## Evidence Hashes

Raw result files remain ignored by Git.

| File | SHA-256 |
| --- | --- |
| `safety_run2/live_context_runs.jsonl` | `a3bb4a8dc6bee004564a6daea52aff0233cdc59f8553f1d5d69520a71ab6bf89` |
| `safety_run2/live_context_summary.json` | `6fdb2b8ed0f382ccdc95bd944cff7b235b1837f7bb9636ec633df43d089abed9` |
| `bright_run1/live_context_runs.jsonl` | `cdc400f5e7f9312662e76b7135ef5697734b02443b7e6cca439616b2c803e60c` |
| `bright_run1/live_context_summary.json` | `21b811d7c46e04e976148be143d71bd941be7eac138ce33f1cbb5412f8f69f02` |
| `dark_run1/live_context_runs.jsonl` | `081da106efc31cdbec3e99e82582b9b8100782c0b2f067eab1ea03b7668dc4ec` |
| `dark_run1/live_context_summary.json` | `088e3bacc717fb6947e755d9bdb8e6f7ddca8e017172d23722364707e4a58ca9` |

## Pending Live-Context Cases

- L03 and L04 remain pending under the historical 100-lux baseline.
- LC01 and LC02 passed under the separately frozen 300-lux deployment-calibrated
  profile. Repeated natural-light calibration is a future task before this value is
  treated as stable.
- The sensor value can vary with sunlight and weather, so each request will retain
  its immediately preceding live context instead of treating earlier readings as a
  precondition.
