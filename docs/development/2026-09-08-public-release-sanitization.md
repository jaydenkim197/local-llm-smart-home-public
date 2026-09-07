# Public Release Sanitization

## Objective

Prepare the tracked project snapshot for public portfolio use while retaining the approved living-room installation photo and keeping private development originals local.

## Work Completed

- Removed the tracked UTM configuration screenshot because it displayed VM network identifiers.
- Preserved a hash-verified copy of that screenshot under the Git-ignored local raw-media directory for the later private report.
- Retained the living-room overview and curtain-controller photos at the user's direction; their public JPEG derivatives contain no indexed GPS coordinates.
- Removed actual Home Assistant, Mac, iPhone, gateway, subnet, MAC, IPv6, and interface identifiers from public-facing text.
- Replaced household router details and internal routing topology with a minimal same-LAN commissioning requirement.
- Replaced location-adjacent solar test coordinates and window azimuth with clearly non-operational fixtures, and made the sunset assertion derive from generated context.
- Replaced personal local filesystem paths and the GitHub account name in reusable documentation with placeholders.
- Changed the Home Assistant URL in `.env.example` to the generic `homeassistant.local` example.
- Removed private-repository wording from the cross-platform workflow.
- Updated stale network documentation to reflect that end-to-end curtain actuation was verified.
- Published the sanitized snapshot as a separate public repository with a new, single-commit Git history: `https://github.com/jaydenkim197/local-llm-smart-home-public`.

## Modified Files

- `.env.example`
- `docs/README.md`
- `docs/architecture/cross_platform_git_workflow.md`
- `docs/architecture/home-assistant-network.md`
- `docs/architecture/physical_iot_integration_plan.md`
- `docs/decisions/ADR-004-temporary-ha-dashboard-relay.md`
- `docs/development/2026-08-29-hardware-arrival.md`
- `docs/development/2026-09-05-home-assistant-vm.md`
- `docs/development/2026-09-05-matter-commissioning-diagnosis.md`
- `docs/development/2026-09-06-ethernet-bridge.md`
- `docs/development/2026-09-06-simulation-and-portfolio-packaging.md`
- `docs/hardware/inventory.md`
- `docs/media/demo-evidence.md`
- `docs/troubleshooting/ha-iphone-network.md`
- `docs/troubleshooting/home-assistant-vm.md`
- `tests/test_outdoor_context.py`
- `tests/test_solar.py`
- `docs/assets/demo/home-assistant-utm.png` (removed)
- `artifacts/demo/raw/home-assistant-utm-original.png` (local, Git-ignored)

## Verification Evidence

- Scanned the tracked working tree for the known actual IPv4, IPv6, MAC, router model, firmware, personal path, repository account, home address, pairing code, school email, and common credential patterns.
- Confirmed `.env` is ignored and has never been tracked.
- Confirmed raw HEIC and MOV evidence remains ignored.
- Confirmed the tracked JPEG assets report no indexed latitude or longitude metadata.
- `.venv/bin/python -m unittest discover -s tests -v` passed all 24 tests after sanitization.
- `bash -n scripts/run.sh` completed successfully.
- `git diff --check` completed without whitespace errors.
- The GitHub repository page shows `Public` and the expected sanitized project files.
- The unauthenticated GitHub API reported `private: false`, `visibility: public`, and `main` as the default branch.
- The public repository was initialized from the sanitized snapshot with no pre-sanitization Git history.

## Unresolved Issues

- Earlier commits in this original private repository still contain the pre-sanitized network documentation and removed UTM screenshot. This repository must remain private unless its history is deliberately rewritten.
- The approved living-room image reveals the interior and exterior view even though its GPS metadata has been removed.

## Next Step

Keep sensitive operational updates in this private repository and copy only reviewed, sanitized snapshots to the public portfolio repository.
