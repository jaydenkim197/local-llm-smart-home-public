# Four-Speaker STT Audit

Date: 2026-09-26. This audit combines the preserved first-run results from the
original local speaker and the three prospective external speaker cohorts for a
descriptive view. It does not replace either [the original single-speaker result](stt-results-2026-09-23.md)
or [the separate prospective result](multispeaker-stt-results-2026-09-26.md).
No model inference was rerun for this audit.

## Inclusion And Quality Review

The user reported four speakers in total. The recording service does not verify
speaker identity. Every cohort has the expected 12 prompts with three takes each:
144 files total. The three external cohorts have 36 matching private Sheet rows
each; the original local cohort was recorded separately. The synthetic receiver
check is not a speaker and was not included.

After collection and after initial evaluation results were known, all 144 local
audio files were audited for filename completeness, nonempty decoded audio,
duration below 0.5 seconds, and RMS below -80 dBFS (an effectively silent file).
These are **post-collection technical review flags**, not pre-registered outcome
filters. No file was missing, unexpected, undecodable, shorter than 0.5 seconds,
or below the silence flag. Therefore no technical exclusion was applied. The audit
does not prove that every participant read the correct prompt or that all speech
is intelligible; those would require blinded manual review.

| Cohort | Files retained | Duration min/median/max | RMS dBFS min/median/max | Technical exclusions |
| --- | ---: | ---: | ---: | ---: |
| Original local | 36 | 1.32 / 2.46 / 3.96 s | -29.2 / -23.4 / -16.5 | 0 |
| External A | 36 | 2.08 / 2.90 / 5.62 s | -29.5 / -25.9 / -22.6 | 0 |
| External B | 36 | 1.92 / 2.79 / 7.44 s | -23.0 / -16.3 / -12.4 | 0 |
| External C | 36 | 2.01 / 2.80 / 4.19 s | -30.7 / -25.7 / -22.5 | 0 |

Pronunciation, accent, or a low STT score is not an exclusion criterion. Removing
cohorts after viewing their scores would inflate the reported accuracy. All four
cohorts remain in the descriptive four-speaker table, and the prospective three
remain separate as the extension's primary aggregate.

## Comparable Inputs And Results

All preserved runs used the same frozen STT dataset SHA-256
`3d0b65da145a3eaa5898a523b6e636d9e04bef9877887d8c63279b8268289737`,
command dataset SHA-256
`80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`,
faster-whisper `tiny.en` CPU/int8, and Ollama `llama3.2:3b` model digest
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`.
The original run used an earlier Git revision; the parser and STT implementation
were unchanged, and the later configurable lux thresholds were explicitly set to
the original 100/800 defaults. All 144 preserved rows were metric-eligible, with
zero fallback rows.

| Cohort | Corpus WER | Transcript exact | Audio-to-gold command | Reference-plan preserved |
| --- | ---: | ---: | ---: | ---: |
| Original local | 22/216 (10.2%) | 22/36 (61.1%) | 30/36 (83.3%) | 33/36 (91.7%) |
| External A | 23/216 (10.6%) | 25/36 (69.4%) | 32/36 (88.9%) | 35/36 (97.2%) |
| External B | 57/216 (26.4%) | 10/36 (27.8%) | 21/36 (58.3%) | 24/36 (66.7%) |
| External C | 11/216 (5.1%) | 29/36 (80.6%) | 29/36 (80.6%) | 32/36 (88.9%) |
| Descriptive four-speaker pooled | 113/864 (13.1%) | 86/144 (59.7%) | 112/144 (77.8%) | 124/144 (86.1%) |

The three **external** cohorts alone had WER 91/648 (14.0%) and audio-to-gold
command match 82/108 (75.9%). Do not report the four-speaker pooled row as if all
four were collected under one controlled protocol: the original used a MacBook
built-in microphone, while external device and room conditions are unknown.

| Descriptive four-speaker slice | Rows | Audio-to-gold command | Reference-plan preserved |
| --- | ---: | ---: | ---: |
| Action required | 120 | 88/120 (73.3%) | 100/120 (83.3%) |
| No-op | 24 | 24/24 (100.0%) | 24/24 (100.0%) |
| Context cooling | 24 | 20/24 (83.3%) | 20/24 (83.3%) |
| Context light | 24 | 21/24 (87.5%) | 21/24 (87.5%) |
| Direct AC | 24 | 22/24 (91.7%) | 22/24 (91.7%) |
| Direct curtain | 36 | 20/36 (55.6%) | 32/36 (88.9%) |
| Scene and global | 24 | 17/24 (70.8%) | 17/24 (70.8%) |
| Unsupported and safety | 12 | 12/12 (100.0%) | 12/12 (100.0%) |

The existing S02 curtain-stop text-planning failure contributes to direct-curtain
gold failures even when the transcript matches the prompt. The external-cohort
report decomposes its failures. No utterance, transcript, gold label, STT model,
or production policy was changed to improve these observed scores.

## Evidence Boundary

The original raw run is in ignored local `results/stt_v1/`; the three prospective
runs are in separate ignored `results/stt_multispeaker_2026-09-26_<private-id>/`
folders. Each run retains its manifest, row-level CSV/JSONL, and per-file audio
SHA-256. The original `audio_runs.jsonl` SHA-256 is
`ad71892259b0af2b6e05030bb8083d790101d93711cb074c4b552e83ebbee880`;
prospective raw-result hashes are in the separate report. Private recordings,
transcripts, and cohort-to-folder mapping were not committed to Git.

This is a small convenience sample, not a population-level estimate of accent,
pronunciation, microphone, or device effects. Any future manual invalid-recording
decision must state a content-independent reason, reviewer, affected case/take,
and both included and excluded sensitivity results. It must not erase the
all-sample first-run result above.
