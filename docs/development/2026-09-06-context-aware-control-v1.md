# Context-Aware Control v1

## Objective

Use actual Home Assistant sensor and curtain state as input to the local LLM while preserving the simulation backend and the curtain-only physical execution boundary. SONOFF, ZBDongle-E, and ZHA are excluded from this phase.

## Reconciliation

- Repository `main` was clean at `e15af87` before this task.
- The repository already recorded M3 commissioning, direct HA curtain close, local Ollama/STT setup, and the first Home Assistant adapter.
- Missing from the repository were the completed long-lived-token setup, authenticated FastAPI physical backend, user-observed FastAPI/LLM close, user-reported open, and command-response state delay.
- `.env` exists locally with the required configuration keys. Values were not printed or committed.
- The physical backend was independently verified through `/api/health` and authenticated HA state reads during this task.

## Work Completed

- Added a request-time state collector using one HA `/api/states` request.
- Normalized temperature, humidity, illuminance, occupancy, and curtain state into a vendor-neutral living-room context.
- Added derived dark, bright, hot, humid, and occupancy flags.
- Added `GET /api/context` and overlaid real HA values onto all corresponding browser device cards.
- Passed the current context and physical actuator allow-list to Ollama for every text and audio request.
- Added deterministic dark/bright curtain interpretation and duplicate open/close suppression.
- Preserved the simulation backend with an equivalent simulated context.
- Exposed the context, full LLM user content, and policy result in the browser LLM trace.
- Consolidated FastAPI on port 8000 with `CONTROL_BACKEND=home_assistant`; Ollama remains local on port 11434.

## Modified Files

- `README.md`
- `app/devices.py`
- `app/main.py`
- `app/models.py`
- `services/home_assistant.py`
- `services/home_context.py`
- `services/parser.py`
- `static/app.js`
- `tests/test_home_assistant.py`
- `docs/README.md`
- `docs/architecture/system_overview.md`
- `docs/decisions/ADR-005-request-time-home-context.md`
- `docs/development/2026-09-06-context-aware-control-v1.md`
- `docs/development/2026-09-06-local-ai-ha-adapter.md`
- `docs/hardware/inventory.md`
- `docs/troubleshooting/ha-state-settling.md`

## Test Evidence

- Ran `.venv/bin/python -m unittest discover -s tests -v`: 8 tests passed. They cover state normalization, one-request HA collection, dark-room planning, redundant-command suppression, physical allow-list filtering, REST service mapping, and state overlay.
- Ran `.venv/bin/python -m compileall app services tests`, `node --check static/app.js`, `bash -n scripts/run.sh`, and `git diff --check`: all completed successfully.
- Verified `.env` is excluded by the repository `.gitignore`.
- `GET /api/health` returned `control_backend=home_assistant` and `home_assistant_configured=true`.
- `GET /api/context` returned live HA values including 27.88 C, 48.21%, 2686.6 lx, motion false, and curtain open at 100%.
- A live LLM request for a dark room while HA reported `is_dark=false` returned no commands.
- A live open request while the curtain was already open returned no commands after policy evaluation.
- A live context-aware request, `It is too bright in here.`, used 1564.9 lx, occupancy true, and curtain open. The normalized plan called `cover.close_cover`; HA moved through `closing` and later reported `closed`, position 0. The user subsequently confirmed the curtain was closed.
- The raw 3B model proposed dimming an unmapped virtual light for the bright-room request. Normalization and the physical actuator boundary replaced it with the allowed curtain action, demonstrating both safety layers.
- Started a temporary simulation server on port 8002. Its health response reported the simulation backend and `/api/context` returned the expected virtual context; the temporary server was then stopped.
- Sent macOS-generated English audio through the physical backend. `faster-whisper:tiny.en` transcribed `close the living room curtain.`, Ollama ran, and the context policy returned no commands because HA already reported `closed`, position 0.

## Unresolved Issues

- Run a real microphone STT request through the physical backend.
- Verify `stop_cover` during movement.
- Decide whether command responses should poll briefly for final cover state or report accepted/moving status.
- Thresholds need later experiments rather than being treated as universal comfort values.

## Next Step

Complete microphone acceptance and representative context evaluation before considering WebSocket caching or autonomous behavior.
