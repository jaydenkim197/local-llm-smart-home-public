# KICS 2026 Fixed STT Evaluation Results

Date: 2026-09-23

## Reproducibility Record

- Input revision: `b024407c220e5a8b27c7e4baa6cd246b4919d3b5`
- STT dataset: `kics_2026_stt_eval_v1`
- STT dataset SHA-256: `3d0b65da145a3eaa5898a523b6e636d9e04bef9877887d8c63279b8268289737`
- Command dataset SHA-256: `80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`
- Speaker/session: `speaker01`
- Recordings: 36, comprising 12 utterances with three takes each
- STT: faster-whisper `tiny.en`, CPU, int8
- Command model: `llama3.2:3b`
- Model digest: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- Fallback, transport failure, or excluded rows: 0

All recordings were collected after the protocol and utterance set were frozen. The
evaluation called the parser but did not apply any command to Home Assistant or a
physical device.

## Overall Results

| Metric | Result |
| --- | ---: |
| Corpus word error rate | 22/216 words (10.2%) |
| Normalized transcript exact match | 22/36 (61.1%) |
| Audio-to-gold command exact match | 30/36 (83.3%) |
| Reference-command preservation | 33/36 (91.7%) |
| Reference-text command exact match | 11/12 cases (91.7%) |

Reference-command preservation compares each audio-path command with the Full
Pipeline command produced from the corresponding written reference. It isolates
voice-path degradation from command-planning failures already present for text.

The difference between 61.1% transcript exact match and 91.7% command preservation
shows that most minor word errors did not change the resulting device command.

## Slice Results

| Slice | Corpus WER | Transcript exact | Audio-to-gold command | Reference command preserved |
| --- | ---: | ---: | ---: | ---: |
| Action required | 19/186 (10.2%) | 17/30 (56.7%) | 24/30 (80.0%) | 27/30 (90.0%) |
| No-op | 3/30 (10.0%) | 5/6 (83.3%) | 6/6 (100.0%) | 6/6 (100.0%) |
| Context cooling | 6/39 (15.4%) | 2/6 (33.3%) | 6/6 (100.0%) | 6/6 (100.0%) |
| Context light | 2/39 (5.1%) | 4/6 (66.7%) | 6/6 (100.0%) | 6/6 (100.0%) |
| Direct AC | 0/27 (0.0%) | 6/6 (100.0%) | 6/6 (100.0%) | 6/6 (100.0%) |
| Direct curtain | 10/60 (16.7%) | 4/9 (44.4%) | 5/9 (55.6%) | 8/9 (88.9%) |
| Scene and global | 4/36 (11.1%) | 3/6 (50.0%) | 4/6 (66.7%) | 4/6 (66.7%) |
| Unsupported and safety | 0/15 (0.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) |

## Failure Decomposition

Six recordings did not match frozen gold commands.

| Case/take | Reference | Transcript | Result | Attribution |
| --- | --- | --- | --- | --- |
| S01/2 | Please lower the living room shade. | Place the work to the living room shade. | No-op instead of curtain close | STT-induced semantic loss |
| S02/1 | Freeze the curtain where it is. | Freeze the cutting where it is. | No-op instead of curtain stop | Existing reference-text planning failure preserved |
| S02/2 | Freeze the curtain where it is. | Freeze the current where it is. | No-op instead of curtain stop | Existing reference-text planning failure preserved |
| S02/3 | Freeze the curtain where it is. | Freeze the curtain, where it is. | No-op instead of curtain stop | Existing reference-text planning failure preserved even with WER 0 |
| S10/2 | Let us settle in for a film. | Let us start off in for a film. | No-op instead of curtain close | STT-induced semantic loss |
| S11/2 | Power up the whole house. | Power up the old house. | AC on only; curtain open missing | STT-induced partial command loss |

Thus, three failures were introduced by the voice path and three repeated the known
S02/C03 text-planning limitation. No production code, prompt, policy, transcript, or
gold label was changed after observing the result.

## Software Latency

| Stage | Mean | Median |
| --- | ---: | ---: |
| faster-whisper transcription | 285.010 ms | 216.709 ms |
| command planning after transcript | 3173.846 ms | 2584.056 ms |

The first transcription call includes model initialization, so the mean is not a
strict warm-only STT latency. These measurements exclude browser recording time,
Home Assistant, network transit, Matter, IR, and physical actuation.

## Local Raw Evidence

Audio and raw traces remain local and ignored by Git. The first result files are
preserved under `results/stt_v1/`.

| File | SHA-256 |
| --- | --- |
| `audio_runs.jsonl` | `ad71892259b0af2b6e05030bb8083d790101d93711cb074c4b552e83ebbee880` |
| `reference_text_runs.jsonl` | `650cf1052ce8e1c538fcce45154171e2f78145320fb02b6e962d41a6f63f3c8d` |
| `run_manifest.json` | `bb45a5ec47cff4cc12cbc784a2db3202fc0c6964d2c3b815e10eef1b38cfcb1f` |
| `stt_eval.csv` | `db6365c1313773b5efca76a65de1b88e44943666dbe99137654a34230ecfe791` |

## Interpretation Boundary

- This is a one-speaker, quiet-room, built-in-microphone feasibility result.
- It does not establish speaker-independent or noisy-room STT performance.
- Another speaker is not required for this frozen v1 claim.
- A stronger speaker-generalization claim requires a separately frozen multi-speaker
  extension rather than adding recordings retrospectively to v1.
