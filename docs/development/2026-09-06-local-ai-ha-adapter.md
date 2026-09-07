# Local AI to Home Assistant Adapter

## Objective

Begin the MacBook local LLM/STT integration without starting deferred SONOFF relay work. Add a safe, narrow path from FastAPI command JSON to the already verified Aqara curtain in Home Assistant.

## Work Completed

- Added `HomeAssistantAdapter` using the standard Home Assistant REST API.
- Mapped logical `cover.living_room_curtain` to confirmed entity `cover.aqara_curtain_controller`.
- Limited physical actions to `open_cover`, `close_cover`, and `stop_cover`.
- Added `CONTROL_BACKEND` configuration. Simulation remains the default; `home_assistant` rejects commands for unmapped devices.
- Added Home Assistant entity-state overlay to the web/API device response.
- Added configuration template and setup guidance for a user-created Home Assistant long-lived access token.
- Updated the browser trace to display the active backend and physical command allow-list.
- Added deterministic direction validation for explicit single-curtain open, close, and stop requests after observing an inverted `open_cover` response from the local model for a close request.

## Modified Files

- `.env.example`
- `README.md`
- `app/config.py`
- `app/main.py`
- `services/home_assistant.py`
- `services/parser.py`
- `scripts/run.sh`
- `static/app.js`
- `static/index.html`
- `tests/test_home_assistant.py`
- `docs/architecture/system_overview.md`
- `docs/decisions/ADR-002-home-assistant-device-layer.md`
- `docs/development/2026-09-06-local-ai-ha-adapter.md`

## Test Evidence

- Initial implementation run: `.venv/bin/python -m unittest discover -s tests -v`: 4 tests passed after the direction-guard test was added.
- Ran `.venv/bin/python -m compileall app services tests`: completed successfully.
- Ran `git diff --check`: no whitespace errors.
- Verified local installation of `faster-whisper` version 1.1.1.
- Started local Ollama and verified installed model `llama3.2:3b` (2.0 GB, Q4_K_M). A real Ollama parsing request reached the model; the first direct close-curtain result was inverted, so it is covered by the new deterministic validation and must be retested.
- Loaded `faster-whisper` model `tiny.en` successfully on CPU with `int8` compute type.
- Ran `POST /api/command/audio` using macOS-generated English audio, “Close the living room curtain.” The STT transcript was `close the living room curtain.`, the LLM mode was `ollama:llama3.2:3b`, the normalized command was `close_cover`, and simulation execution succeeded.
- Ran `POST /api/command/text` after the direction validation. Ollama output was normalized to `close_cover` and simulation execution succeeded.
- Later user-provided recovery evidence confirms `.env` configuration, authenticated HA REST state reads, and FastAPI/Ollama `close_cover` execution. The response reported `result.success=true`, and the user observed the physical curtain close.
- The recovery summary reports `open_cover` also completed, but its command output and direct observation are not present in the pasted transcript; it is recorded as user-reported rather than independently reproduced here.

## Unresolved Issues

- Verify `stop_cover` through the FastAPI adapter.
- Complete a microphone-originated STT to physical-curtain test; the existing STT test used macOS-generated audio.
- Command responses can briefly show the pre-command HA state while a Matter cover is moving.

## Next Step

Build request-time context-aware control using the verified Aqara sensor and curtain states while retaining the physical actuator allow-list.
