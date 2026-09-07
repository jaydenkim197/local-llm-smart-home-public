# Project Documentation

This directory preserves the development history and current technical state of the Local LLM Smart Home project.

## Documentation Map

- [System Overview](architecture/system_overview.md): Current software and hardware integration structure.
- [Physical IoT Integration Plan](architecture/physical_iot_integration_plan.md): Target architecture and bring-up sequence for Aqara M3, ZBDongle-E, and Home Assistant.
- [Cross-Platform Git Workflow](architecture/cross_platform_git_workflow.md): Safe handoff process between Mac and Windows.
- [Hardware Inventory](hardware/inventory.md): Actual device models, connection methods, and verification status.
- [ADR-001: Local AI Runtime](decisions/ADR-001-local-ai-runtime.md): Why the project uses local Ollama and faster-whisper.
- [ADR-002: Home Assistant Device Layer](decisions/ADR-002-home-assistant-device-layer.md): Why Home Assistant normalizes physical Aqara and SONOFF devices.
- [ADR-005: Request-Time Home Context](decisions/ADR-005-request-time-home-context.md): How live HA state reaches the local LLM without vendor coupling.
- [ADR-006: Local Solar Context](decisions/ADR-006-local-solar-context.md): Why sunrise, sunset, and sun position are calculated locally with private coordinates.
- [ADR-007: Cached Open-Meteo Context](decisions/ADR-007-cached-open-meteo-context.md): Why outdoor weather and radiation are cached and isolated from local control.
- [ADR-008: Aqara IR AC Scene Sync](decisions/ADR-008-ir-ac-scene-sync.md): Why fixed Matter Scene Sync switches provide bounded IR AC control.
- [Development Log: Hardware Arrival](development/2026-08-29-hardware-arrival.md): Transition from simulator development to hardware integration.
- [Development Log: Physical IoT Plan](development/2026-09-05-physical-iot-plan.md): Approved architecture and first hardware milestone.
- [Development Log: Context-Aware Control v1](development/2026-09-06-context-aware-control-v1.md): Live state collection, LLM context injection, and physical policy validation.
- [Development Log: Local Solar Context](development/2026-09-06-solar-context.md): Location handling, solar calculations, and LLM integration.
- [Development Log: Demo MVP Stabilization](development/2026-09-06-demo-mvp-stabilization.md): Physical demo UI, outdoor context, no-op consistency, and state settling.
- [Development Log: M3 IR AC Matter Diagnosis](development/2026-09-06-m3-ir-ac-matter-diagnosis.md): Why the Aqara IR AC is not yet a Home Assistant climate actuator.
- [Development Log: Aqara IR AC Scene Sync](development/2026-09-06-ac-scene-sync-control.md): Discovery and safe mapping of the IR AC scene commands.
- [Development Log: Demo MVP Completion](development/2026-09-06-demo-mvp-completion.md): Final filmed microphone, curtain, and AC physical acceptance.
- [Development Log: Simulation and Portfolio Packaging](development/2026-09-06-simulation-and-portfolio-packaging.md): Offline simulation coverage, final report, portfolio summary, and demo media organization.
- [Development Log: Mobile Demo Media Packaging](development/2026-09-07-mobile-demo-media.md): Phone photos, physical demo videos, public JPEG conversion, and privacy handling.
- [Development Log: Public Release Sanitization](development/2026-09-08-public-release-sanitization.md): Removal and masking of local network, router, filesystem, and account identifiers.
- [Final MVP Report](reports/2026-09-06-mvp-final-report.ko.md): Korean implementation and verification report.
- [Portfolio Summary](portfolio/project-summary.ko.md): Concise problem, solution, contribution, and result summary.
- [Demo Media Catalog](media/demo-evidence.md): Selected evidence, captions, raw recording metadata, and publication cautions.
- [Experiment Template](experiments/README.md): Format for functional and performance tests.
- [Troubleshooting Guide](troubleshooting/README.md): Format for recurring setup and integration issues.
- [M3 IR AC Not Exposed](troubleshooting/m3-ir-ac-not-exposed.md): Evidence and safe next checks when the M3 bridge does not publish its IR AC.

## Operating Rule

Each meaningful implementation task should leave two kinds of evidence:

1. A chronological development log with the actual work and test outcome.
2. A promoted document when it establishes a lasting decision, current architecture, hardware configuration, experiment result, or reusable fix.

Do not record unmeasured performance claims or unverified hardware behavior.
