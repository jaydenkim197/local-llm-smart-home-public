# Prospective Multi-Speaker STT Evaluation

Date: 2026-09-26. This is a separate extension of the frozen single-speaker
experiment, not a retrospective addition to its original result.

## Inputs And Collection Audit

- The user reported three additional people completed the same 12 English prompts,
  three takes each. The collection service does not verify speaker identity.
- Three private Drive folders each contained the complete 36-file set; the private
  submission Sheet contained 36 matching rows per folder. No duplicate or missing
  case/take was found.
- All 108 files were stored as `audio/webm`. Local downloads matched the Drive-listed
  byte counts, and PyAV decoded audio frames from every file. File size and decoding
  do not establish speech quality or independently verify speaker identity.
- The synthetic `P-SYNTHCHECK1` receiver test was excluded. Raw voice recordings,
  transcripts, per-row traces, and the private cohort-to-folder mapping are not in Git.

| Prospective cohort | Files | Total bytes | Decoded duration range |
| --- | ---: | ---: | ---: |
| A | 36 | 1,272,584 | 2.078-5.617 s |
| B | 36 | 665,594 | 1.920-7.440 s |
| C | 36 | 1,276,769 | 2.013-4.190 s |

## Fixed Evaluation Environment

- Input code revision: `52a26fdebb9680fa8311dbe3d6cef0ab92823d03`.
- STT dataset `kics_2026_stt_eval_v1` SHA-256:
  `3d0b65da145a3eaa5898a523b6e636d9e04bef9877887d8c63279b8268289737`.
- Command dataset SHA-256:
  `80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`.
- MacBook Air M1; faster-whisper `tiny.en`, CPU/int8; local Ollama
  `llama3.2:3b`, digest
  `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`.
- Frozen 100-lux dark and 800-lux bright evaluation defaults; simulation backend.
  Each clip used the same synthetic context as its frozen source command case.
- All 108 audio rows were metric-eligible. Fallback, parser error, and excluded row
  counts were zero. The runner produced commands but did not apply them to Home
  Assistant or physical devices.

## Results

WER is total word edits divided by reference words. Command exact match compares
the final command multiset to frozen gold. Preservation compares the audio-path plan
to a fresh reference-text plan for the same case. These are different measures.

| Cohort | Corpus WER | Transcript exact | Audio-to-gold command | Reference-plan preserved |
| --- | ---: | ---: | ---: | ---: |
| A | 23/216 (10.6%) | 25/36 (69.4%) | 32/36 (88.9%) | 35/36 (97.2%) |
| B | 57/216 (26.4%) | 10/36 (27.8%) | 21/36 (58.3%) | 24/36 (66.7%) |
| C | 11/216 (5.1%) | 29/36 (80.6%) | 29/36 (80.6%) | 32/36 (88.9%) |
| Prospective pooled | 91/648 (14.0%) | 64/108 (59.3%) | 82/108 (75.9%) | 91/108 (84.3%) |

The original `speaker01` result remains separate: WER 22/216 (10.2%),
audio-to-gold 30/36 (83.3%), and preservation 33/36 (91.7%). It used the same
dataset hashes, model digest, and parser, but a local built-in microphone rather
than this external collection path. Do not silently merge it into the prospective
pooled result.

| Prospective slice | Rows | Audio-to-gold command | Reference-plan preserved |
| --- | ---: | ---: | ---: |
| Action required | 90 | 64/90 (71.1%) | 73/90 (81.1%) |
| No-op | 18 | 18/18 (100.0%) | 18/18 (100.0%) |
| Context cooling | 18 | 14/18 (77.8%) | 14/18 (77.8%) |
| Context light | 18 | 15/18 (83.3%) | 15/18 (83.3%) |
| Direct AC | 18 | 16/18 (88.9%) | 16/18 (88.9%) |
| Direct curtain | 27 | 15/27 (55.6%) | 24/27 (88.9%) |
| Scene and global | 18 | 13/18 (72.2%) | 13/18 (72.2%) |
| Unsupported and safety | 9 | 9/9 (100.0%) | 9/9 (100.0%) |

Mean/median local STT times were 310.6/269.8 ms; mean/median post-transcript
planning times were 3173.5/2536.8 ms. The first STT call includes model
initialization. These timings exclude browser recording, upload, Home Assistant,
network transit, Matter, IR, and physical actuation.

## Failure Decomposition

There were 26 audio-to-gold failures. Nine were S02 (curtain stop) across all
cohorts. Its freshly parsed reference text also failed, so those nine cannot be
attributed to STT alone. The other 17 did not preserve the corresponding
reference-text command plan. They occurred in S01 (3), S05 (2), S06 (4), S09 (3),
S10 (2), and S11 (3). Most involved changed content words in the transcript.
One S11 failure had zero normalized WER yet lost the curtain action; punctuation,
casing, or nondeterministic command planning may contribute, so it is not labeled
as a lexical STT error.

Cohort B accounts for 15/26 total command failures and has the highest WER.
Because microphone models, rooms, network conditions, and individual identities
were not collected or controlled, this small convenience sample does not establish
population-level speaker-independent accuracy or a device effect. No prompt,
production rule, gold label, or transcript was changed after seeing these results.

## Preserved Raw Evidence

Each cohort has an ignored local `results/stt_multispeaker_2026-09-26_<private-id>/`
directory with `audio_runs.jsonl`, `reference_text_runs.jsonl`, `stt_eval.csv`,
`run_manifest.json`, and `summary.md`. Each audio row includes the local audio
SHA-256. The private audio remains under ignored `data/kics_2026_stt/`.

| Cohort | `audio_runs.jsonl` SHA-256 | `run_manifest.json` SHA-256 |
| --- | --- | --- |
| A | `be19848642c459b16167d5441c372dc37a775e5135970a173abc144ecd45b0db` | `3b9fd77e0562b964a1aea26b34a395b03e534c308dcb87b89feb1ee6244d0ebc` |
| B | `f68680a3015d9a321a057d9c127e89950959b879096c0e7d02dd848f81079f33` | `7ef0494296dfc59933c342bc6d2c1cc374385d1c887a7968725422d41e2bc938` |
| C | `2ad61beb468fd271566a0a495f6df3acd0e5e89f942ba6fcb44181f4777c1223` | `0b7817aee504e5ba40f9cf11f37db59f73e6a52bee1131b552aa61c72901e963` |

Next work, outside this evaluation: review anomalous clips and optionally collect
participant-reported device/room information with their consent. Any changed STT
model or parser is a new experiment, not a correction to these first-run results.
