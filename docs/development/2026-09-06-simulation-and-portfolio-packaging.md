# Simulation and Portfolio Packaging

## Objective

Strengthen development without the physical test environment, reconcile the public README with the completed MVP, and organize the final recording and screenshots for reporting and portfolio use.

## Work Completed

- Made the simulation backend provide its actual controllable entity set to the parser and policy layer.
- Added simulation API integration coverage for movie mode, whole-home-on behavior, context-based cooling suppression, and reset behavior.
- Added an explicit backend argument to `scripts/run.sh` so an existing physical `.env` cannot accidentally override a requested simulation run.
- Rewrote the root README around the implemented context-aware controller rather than the original simulator-only prototype.
- Added a Korean final MVP report and portfolio summary.
- Added a demo media catalog with captions, metadata, inclusion decisions, and public-sharing cautions.
- Selected a dashboard still from the final recording as repository-safe evidence. The UTM screenshot was later removed during public-release sanitization.
- Preserved the original final recording locally under `artifacts/demo/` while excluding the large binary from Git history.

## Modified Files

- `.gitignore`
- `README.md`
- `app/devices.py`
- `app/main.py`
- `scripts/run.sh`
- `tests/test_simulation_api.py`
- `docs/README.md`
- `docs/architecture/system_overview.md`
- `docs/reports/2026-09-06-mvp-final-report.ko.md`
- `docs/portfolio/project-summary.ko.md`
- `docs/media/demo-evidence.md`
- `docs/assets/demo/context-aware-dashboard.png`
- `artifacts/demo/README.md`
- `artifacts/demo/final-physical-acceptance-2026-09-06.mov` (local, Git-ignored)

## Test Evidence

- Baseline before changes: `.venv/bin/python -m unittest discover -s tests -v` passed 20 tests.
- Post-change: `.venv/bin/python -m unittest discover -s tests -v` passed 24 tests.
- `bash -n scripts/run.sh` completed successfully.
- `git diff --check` completed without whitespace errors.
- Started `./scripts/run.sh simulation` and observed `/api/health` return HTTP 200 with `control_backend=simulation`; Home Assistant and Ollama were both reported unreachable as expected in the offline environment.
- Sent `I am going to watch a movie from now on.` to `/api/command/text` and observed HTTP 200, fallback parsing, `movie_mode`, successful application, TV `on`, curtain `closed`, and robot cleaner `stopped`.
- Reset the simulated devices and shut down the temporary Uvicorn process normally after the smoke test.
- Media inspection sampled the final recording at 0, 25, 50, 75, 100, 125, and 150 seconds.
- Recording metadata observed with macOS metadata tools: H.264, 2880 x 1800, 153.86 seconds, 25,469,001 bytes.

## Unresolved Issues

- The raw screen recording includes a short ChatGPT-page segment and visible browser profile chrome. It should be trimmed or cropped before public publication.
- Physical device behavior was not retested because this work was performed away from the test environment.

## Next Step

Use the report, portfolio summary, selected stills, and local recording for submission packaging. Perform any new physical acceptance test only after returning to the Home Assistant and Aqara network.
