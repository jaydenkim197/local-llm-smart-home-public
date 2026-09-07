# Local Solar Context

## Objective

Add current sunrise, sunset, daylight, and sun-position information to the LLM's HomeContext without exposing the user's precise home location or depending on a remote API.

## Work Completed

- Confirmed the address corresponds to the intended apartment complex through public address and map sources.
- Inspected the target building on a north-up map. It has a three-wing layout with multiple facade directions, so no single living-room direction was inferred from the building number alone.
- Confirmed Home Assistant `sun.sun` was available but HA's global coordinates still pointed to a default city location.
- Added Astral 3.2 for local solar calculation.
- Added private local coordinate, elevation, timezone, and optional window-azimuth settings. Exact coordinates remain only in `.env`.
- Added sunrise, sunset, daylight state, solar azimuth/elevation, next event, and minutes-until-event to every HomeContext snapshot.
- Added sun-to-window alignment fields and later configured the user-measured southwest window direction in local `.env` only.
- Added deterministic normalization for direct sunrise/sunset questions after the first 3B model response copied the sunrise time into a sunset answer.
- Redirected the user's browser from the stopped port 8001 instance to the active physical backend on port 8000.

## Modified Files

- `.env` (ignored local configuration only)
- `.env.example`
- `requirements.txt`
- `app/config.py`
- `services/home_context.py`
- `services/solar.py`
- `services/parser.py`
- `tests/test_solar.py`
- `README.md`
- `docs/architecture/system_overview.md`
- `docs/decisions/ADR-006-local-solar-context.md`
- `docs/development/2026-09-06-solar-context.md`
- `docs/development/2026-09-06-context-aware-control-v1.md`
- `docs/hardware/inventory.md`

## Test Evidence

- Unit tests verify local sunrise/sunset generation, daylight state, angular wraparound, unknown window direction, and deterministic sunset response.
- Initial live context at 12:27 Asia/Seoul reported sunrise 06:01, sunset 18:47, daylight true, solar azimuth 181.21 degrees, elevation 60.38 degrees, and 380 minutes until sunset.
- The first live Ollama response to `What time is sunset today?` incorrectly answered `6:01 PM`. The trace showed the correct 18:47 context value. After deterministic normalization, the API returned `Today's sunset is at 18:47 Asia/Seoul.` with no physical commands.
- With HA reporting the curtain closed at position 0 and illuminance 876 lux, a live `It is too bright in here.` request returned `context_no_action`, no commands, and `The curtain is already closed.` No physical action was sent.
- The active FastAPI health endpoint on port 8000 reported the Home Assistant backend configured. Port 8001 had no listening server before the browser redirect.

## Unresolved Issues

- Elevation is currently zero because a verified local ground/building elevation was not collected; this has a small effect on astronomical horizon timing.
- Evaluate how solar and outdoor-radiation context should influence curtain policy together with indoor illuminance.

## Next Step

Collect repeatable observations before promoting sun-window alignment or outdoor radiation from LLM context to deterministic curtain policy.
