# KICS 2026 Physical End-to-End Protocol

Date frozen: 2026-09-25

## Research Question

Can a fixed English voice recording travel through the deployed local STT, live Home
Context, local LLM, policy boundary, Home Assistant, Matter bridge, and physical
actuator path without losing the intended command?

## Fixed Scope

The fixed cases are in `physical_e2e_cases.json`. Each case is repeated three times in
the declared order:

1. Curtain open from a verified closed state.
2. Curtain close from a verified open state.
3. Send the Aqara M3 IR `AC Cool 24` preset.
4. Send the Aqara M3 IR `AC Off` preset.

The curtain pair naturally restores its own precondition for the next repetition. The
AC pair leaves the air conditioner off after each repetition.

## Measured Path

```text
stored WebM recording
  -> FastAPI /api/command/audio
  -> faster-whisper tiny.en
  -> live Home Assistant context
  -> local llama3.2:3b
  -> normalization / policy / physical allow-list
  -> Home Assistant REST service
  -> Matter / Aqara Hub M3
  -> curtain or IR scene
```

The client API wall time begins immediately before the HTTP upload and ends after the
FastAPI response is fully received. It includes file upload on loopback, STT, live
context collection, command planning, Home Assistant calls, and the adapter's curtain
settling wait. A separate curtain physical-settle time continues polling live Home
Assistant state for up to 30 seconds after the response if necessary. Both exclude
browser microphone capture, speaking time, and any delay before the fixed audio file
was submitted.

## Verification Boundary

- Curtain success requires the expected command, a successful apply result, and the
  expected live Home Assistant cover state within the runner's post-response settling
  window. The adapter's shorter `settled` result is retained separately rather than
  overriding a later verified final state.
- AC command acceptance requires the expected command and successful Scene Sync
  service calls.
- AC physical success additionally requires a human observation entered with
  `--observe-ac`. A successful HTTP response or Matter switch edge must never be
  reported as the physical AC state.
- The runner refuses to execute unless `--allow-actuation` is supplied.
- AC cases are excluded unless `--include-ac` is supplied.
- A failed physical precondition is recorded as ineligible and is not repaired by a
  hidden setup command.
- Each completed row is persisted immediately. The default behavior stops after a
  failed precondition or physical verification so repeated commands cannot hide or
  compound the first failure. `--continue-on-failure` is diagnostic-only.

## Execution

Start Home Assistant, Ollama, and the physical FastAPI backend, then run:

```bash
.venv/bin/python docs/experiments/kics_2026/run_physical_e2e.py \
  --allow-actuation \
  --output-dir docs/experiments/kics_2026/results/physical_e2e_v1/curtain
```

This default run executes only the curtain pair. Run the IR cases with an observer:

```bash
.venv/bin/python docs/experiments/kics_2026/run_physical_e2e.py \
  --allow-actuation --include-ac --observe-ac \
  --case P03 --case P04 \
  --output-dir docs/experiments/kics_2026/results/physical_e2e_v1/ac
```

Raw outputs remain ignored by Git. A reviewed aggregate may be committed later with
the dataset hash, input revision, observed counts, and explicit interpretation
limits.

## Interpretation

This is a single-home, single-speaker, fixed-recording deployment check. It is not a
general physical-device benchmark. First-call latency is retained because model
initialization is part of a freshly started deployed session; later repetitions are
reported separately rather than silently discarding the first observation.
