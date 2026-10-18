# KICS 2026 Physical End-to-End Results

Date: 2026-09-25

## Reproducibility Record

- Dataset: `kics_2026_physical_e2e_v1`
- Dataset SHA-256: `844faa2753334dee524616a17b7968a59b47a7f4cd74a1e58ea2449daa9bc341`
- Input: fixed English WebM recordings uploaded to the production
  `/api/command/audio` endpoint
- STT: `faster-whisper tiny.en`
- LLM: `llama3.2:3b`
- Backend: deployed Home Assistant adapter, Matter bridge, Aqara Hub M3

The curtain run used code revision `21fabff86f52c1887ac8f09507dbad1ace3c0136`.
The subsequent single-trigger IR AC acceptance used revision
`aba6dbb4375096d8d6e388ca10e7d64c75c8a558` after the Scene trigger correction.

## Curtain Audio-to-Physical-State Trial

Two fixed audio cases were run three times each in alternating order: curtain open
from a verified closed state, then curtain close from a verified open state.

| Metric | Result |
| --- | ---: |
| Eligible trials | 6/6 |
| Expected command exact match | 6/6 |
| Home Assistant apply accepted | 6/6 |
| Final Home Assistant curtain state verified | 6/6 |
| API wall time, mean / median | 20,838.821 / 20,101.896 ms |
| API wall time, min / max | 18,975.077 / 26,270.510 ms |
| Curtain state settle time, mean / median | 20,884.520 / 20,147.498 ms |
| Curtain state settle time, min / max | 19,022.625 / 26,314.860 ms |

API wall time covers fixed-file upload, STT, live HomeContext, local LLM, policy,
Home Assistant calls, and the adapter's initial settling wait. Curtain settle time
continues polling Home Assistant after the API response when required. Both exclude
browser recording, user speaking time, and a human visual observation timestamp.

## IR AC Single-Trigger Acceptance

The Aqara `AC Cool 24` Scene was updated in Aqara Home to send a 24 C preset. The
adapter then used the revised on-edge-only semantics:

```text
logical AC on  -> AC Off Scene once -> 2 s -> AC Cool 24 Scene once
logical AC off -> AC Off Scene once
```

| Case | Command exact / accepted | Physical evidence | API wall time |
| --- | --- | --- | ---: |
| `P03` AC Cool 24 | 1/1 / 1/1 | User observed one Off Scene followed by startup at 24 C | 14,185.420 ms |
| `P04` AC Off | 1/1 / 1/1 | User observed shutdown after one Off Scene | 4,501.657 ms |

The AC figures are single acceptance observations, not repeated reliability or
physical-latency measurements. The system still has no trustworthy return channel for
AC power, mode, or setpoint; physical results are user observations rather than a
Home Assistant state claim.

## Controlled IR Follow-up

An attempted interactive repeat runner could not receive its terminal observation
input after its first AC-on event, so it did not advance to its planned AC-off event.
That incomplete attempt is excluded rather than classified as a device failure.

The follow-up used three independent text endpoint calls with direct Home Assistant
Scene Sync timestamp checks and an operator observation after each physical response:

| Event | Logical command | Scene sequence | Operator observation |
| --- | --- | --- | --- |
| R01 | AC off | `AC Off` once | AC off |
| R02 | AC on | `AC Off` once -> approximately 2 s -> `AC Cool 24` once | AC on at Cool 24 preset |
| R03 | AC off | `AC Off` once | AC off |

The adapter returned no errors for all three calls, and the relevant Scene Sync
switches changed in Home Assistant for every dispatched scene. This adds one
controlled complete ON/OFF follow-up sequence to the earlier acceptance evidence; it
does not establish a statistical IR reliability rate or physical latency.

## Raw Evidence Hashes

Raw JSONL and summary files are intentionally ignored by Git. Their first-observation
hashes are preserved locally:

| Run | File | SHA-256 |
| --- | --- | --- |
| Curtain | `physical_runs.jsonl` | `558d6406f425542728b4b0a14f152c173c33e160751dd86d51f6b20aaa6108f2` |
| Curtain | `physical_summary.json` | `ecef1e697207da06719d78d0d78836e3ae606dad087835971b39b1e776c7aeb3` |
| AC Cool 24 | `physical_runs.jsonl` | `9eff78c7fd73e7f707a1fa628daee002cc9191a4fd6531a16a31fa52fb8a128e` |
| AC Cool 24 | `physical_summary.json` | `c047f5653074788a98edfd058bbbe9ffc4b749366f32e65493eb479ac0c95ecc` |
| AC Off | `physical_runs.jsonl` | `4f6f4df516c2159174c767768b895ba398e0a3dcc1144217f9d0bdc1aaa41cff` |
| AC Off | `physical_summary.json` | `741e25eb7355d32a72d57f91099901246ea7af12121e6667a75ad0880e7d4baa` |
| Controlled IR follow-up | `controlled_ir_observations.json` | `857bc89da7c55c013c77af3ed792b78fd760f692d839e76cf9feae8fa9212e97` |

## Interpretation Boundary

- This is a single-home, fixed-recording deployment check.
- The curtain result verifies the Home Assistant state transition, not an external
  camera-based physical completion timestamp.
- The AC result is one user-observed acceptance per action after a Scene semantic
  correction, not a repeated statistical evaluation.
- Do not combine these API times with the earlier warm command-planning latency,
  because the measurement boundaries differ.
