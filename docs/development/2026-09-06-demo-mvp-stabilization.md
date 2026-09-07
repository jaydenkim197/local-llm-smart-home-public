# Demo MVP Stabilization

## Objective

Prepare the request-time context-aware curtain controller for a clear one-to-two-minute demonstration using the actual Aqara sensors, local STT/LLM, and Home Assistant path.

## Work Completed

- Removed the motion sensor from current HomeContext, the physical device overlay, and the demo UI after the user excluded it from scope.
- Configured the user-measured southwest living-room window direction in ignored local `.env` only.
- Added cached Open-Meteo outdoor weather, cloud, precipitation, wind, and solar-radiation context with failure isolation.
- Reordered bright-room no-op policy so a closed curtain consistently returns `The curtain is already closed.` even when illuminance crosses the bright threshold.
- Added bounded Home Assistant cover-state polling and exposed confirmed versus still-updating execution state.
- Replaced the virtual-device dashboard with a physical demo view showing actual indoor readings, curtain state, solar/window relation, outdoor context, input/transcript, response, validated action, and execution status.
- Kept the full model trace in a collapsed technical-details section.
- Changed health indicators to check actual Home Assistant and Ollama reachability.

## Modified Files

- `.env` (ignored local configuration only)
- `.env.example`
- `app/config.py`
- `app/devices.py`
- `app/main.py`
- `services/home_assistant.py`
- `services/home_context.py`
- `services/outdoor_context.py`
- `services/parser.py`
- `static/index.html`
- `static/app.js`
- `static/styles.css`
- `tests/test_home_assistant.py`
- `tests/test_outdoor_context.py`
- `tests/test_solar.py`
- Project documentation listed in the Git diff

## Test Evidence

- Python unit suite passed 14 tests after the implementation.
- JavaScript syntax check, Python compile check, and Git whitespace check passed.
- Live `/api/context` returned actual HA indoor values without a motion field, the locally configured window alignment, and a fresh Open-Meteo response.
- Live Open-Meteo context reported outdoor temperature 25.5 C, cloud cover 34%, direct radiation 106.2 W/m2, and precipitation probability 10% at the observed time.
- Browser inspection confirmed the new dashboard displayed actual values and the intended three-step flow.
- Browser text acceptance with the curtain already closed returned `context_no_action`, `The curtain is already closed.`, `No physical action`, and `Safely suppressed - no-op`.
- A live text command traversed Ollama, FastAPI, Home Assistant, Matter, and the Aqara curtain. HA confirmed the explicit open at `open`, position 100 after bounded polling.
- A following `It is too bright in here.` request used 971 lux, current solar/window relation, and Open-Meteo context; it produced `reduce_natural_light` and HA confirmed `closed`, position 0. This is HA state evidence; direct user observation of these two movements was not collected in this task.

## Unresolved Issues

- Outdoor and solar values are not yet deterministic curtain triggers; observations are needed before defining thresholds.
- This stabilization record initially lacked direct final acceptance. Final browser microphone, curtain, and AC physical acceptance was completed later and is recorded in `2026-09-06-demo-mvp-completion.md`.

## Next Step

The recording milestone is complete. Preserve this implementation while planning autonomous control or edge-device migration separately.
