# ADR-013: Deployed Illuminance Calibration

## Status

Accepted and implemented on 2026-09-25.

## Context

The reproducible evaluation baseline classifies illuminance below 100 lux as dark.
During physical-site preparation, the installed Aqara illuminance sensor reported
235 lux after the user established a visibly low-light room condition. The user
identified 100 lux as effectively a night-time or near-total-occlusion condition for
this room, not an appropriate natural-light intervention threshold.

Changing the global default would silently reinterpret frozen 40-case and held-out
results. Treating the observed 235-lux reading as an automatic physical success would
also be invalid under the existing policy.

## Decision

- Keep source defaults at 100 lux dark and 800 lux bright, preserving historical
  evaluation semantics.
- Make the two illuminance thresholds explicit local deployment configuration.
- Set the ignored deployed `.env` profile to a provisional dark threshold of 300 lux
  and retain the 800-lux bright threshold.
- Freeze a separate calibrated-v2 live-context dataset before executing it.
- Describe the 300-lux value as a single-room calibration candidate, not a universal
  lighting-comfort standard.

## Consequences

- Historical command and held-out results remain tied to their 100-lux baseline.
- Physical live-context evidence must state the active threshold profile and may not
  be pooled unqualified with baseline evaluation results.
- A future calibration study should use repeated readings across time, weather, and
  sensor placement before treating this threshold as stable.
