# KICS 2026 Fixed STT Protocol

## Scope

This experiment evaluates the local English voice path:

```text
fixed spoken utterance
-> faster-whisper tiny.en
-> transcript
-> frozen Full Pipeline command planning
```

It does not send commands to Home Assistant and does not measure Matter, IR, or
physical device latency.

## Fixed Input

- 12 utterances selected from frozen `cases.json`
- 3 takes per utterance
- 36 recordings total
- 1 speaker
- quiet indoor room
- MacBook built-in microphone
- natural pace and volume
- approximately 0.5 seconds of silence before and after speaking
- punctuation is not dictated

The source cases cover direct curtain, direct AC, contextual cooling, contextual
light, scene/global, and unsupported requests. The manifest is `stt_cases.json`.

## Recording

Start the experiment-only recorder from the repository root:

```bash
.venv/bin/python docs/experiments/kics_2026/record_stt_set.py
```

Open `http://127.0.0.1:8010`, keep the default pseudonymous speaker ID
`speaker01`, and complete the prompts in order. The tool stores files under:

```text
data/kics_2026_stt/speaker01/S01_take01.webm
...
data/kics_2026_stt/speaker01/S12_take03.webm
```

Do not rehearse selectively or delete a poor take after seeing a transcript. If a
recording is unusable because of interruption or device failure, restart the whole
recording set under a new speaker/session ID and document the reason.
The recorder refuses to overwrite an existing take.

## Execution

After all 36 clips exist, start Ollama and run:

```bash
.venv/bin/python docs/experiments/kics_2026/run_stt_eval.py \
  --speaker-id speaker01 \
  --output-dir docs/experiments/kics_2026/results/stt_v1

.venv/bin/python docs/experiments/kics_2026/summarize_stt_results.py \
  docs/experiments/kics_2026/results/stt_v1/stt_eval.csv \
  --output docs/experiments/kics_2026/results/stt_v1/summary.md
```

The runner refuses to begin when any clip is missing and refuses to overwrite an
existing result set.

## Metrics

- Corpus WER: total word-level edit distance divided by total reference words
- Transcript exact match after lowercase and punctuation normalization
- Audio-to-gold command exact match
- Reference-command preservation: audio command versus the same case's reference-text
  Full Pipeline command
- faster-whisper transcription latency
- command-planning latency after transcription
- fallback/error/excluded row count

Always report overall, action-required, no-op, and category slices. Audio results are
not evidence of physical actuation.
