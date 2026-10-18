# ADR-011: Fixed STT Evaluation Protocol

## Status

Accepted on 2026-09-20 before audio collection.

## Context

The command-planning experiments use text input and therefore do not measure the
browser microphone and faster-whisper stage. Reusing ad hoc demo recordings would
not provide a fixed script, repeated takes, or a clean distinction between
transcription errors and command-planning errors.

## Decision

Use a frozen 12-utterance subset of the original requirements-based command dataset.
Record three takes per utterance from one speaker, producing 36 clips. Keep the
wording, order, microphone, environment, and delivery instructions fixed before
recording.

Report corpus word error rate, normalized transcript exact match, final command exact
match against frozen gold, and whether the audio-path command preserves the command
produced from the reference text. Record transcription and command-planning software
latency separately. Do not invoke Home Assistant or apply physical commands during
this experiment.

The source utterances are intentionally known command requirements. This evaluation
measures voice-path robustness, not unseen language generalization. The separate
20-case prospective text set remains the generalization check.

Audio and raw traces remain local and ignored by Git. Publish aggregate metrics and
cryptographic hashes unless explicit consent is given to publish a recording.

## Consequences

- One speaker and one quiet-room session limit external validity.
- Three takes provide within-session repetition but not speaker diversity.
- Comparing audio output with both gold and the reference-text pipeline helps
  separate STT degradation from an existing command-planning failure.
- A later multi-speaker or noisy-room study requires a new versioned protocol.
