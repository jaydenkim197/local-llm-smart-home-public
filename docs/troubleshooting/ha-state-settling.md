# Home Assistant Cover State Settling

## Symptom

A successful FastAPI response can still contain the curtain's pre-command state, or HA can report `closing` with the old position for several seconds.

## Confirmed Evidence

- A prior FastAPI close returned successful service execution while the embedded device snapshot still showed `open`, position 100; the user observed physical closing.
- On 2026-09-06, a context-aware close changed HA to `closing`, position 100 for at least 10 seconds. A later request reported `closed`, position 0.

## Interpretation

The Home Assistant service call acknowledges command acceptance before Matter movement and state reporting have settled. A successful service response is not proof that the final physical position has already been reached.

## Current Handling

After Home Assistant accepts an open or close service call, the adapter polls the mapped cover entity for up to 15 seconds. Execution output distinguishes a confirmed final state from an accepted command whose state is still updating. Stop commands return after acceptance because they have no single final open/closed target.

The pre-command HomeContext remains preserved in the LLM trace, while the UI overlays the latest post-command curtain state.
