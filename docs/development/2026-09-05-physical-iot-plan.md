# Development Log: Physical IoT Integration Plan

Date: 2026-09-05

## Objective

Establish the approved architecture and safe execution order for integrating Aqara M3 devices and SONOFF Zigbee relays with the existing local LLM smart-home simulator.

## Work Completed

- Moved the physical IoT workflow into the architecture documentation area.
- Defined Home Assistant OS on the MacBook VM as the physical-device abstraction layer.
- Defined separate integration paths for Aqara M3 Matter Bridge and ZBDongle-E/ZHA.
- Preserved the simulation path as a required regression and fallback mode.
- Narrowed the immediate milestone to Home Assistant VM, M3 Matter Bridge, one sensor, and the curtain.
- Corrected the LLM action example to the existing `close_cover` command schema.
- Reordered the plan so Aqara Matter verification occurs before SONOFF mains installation and adapter work.

## Modified Files

- `docs/architecture/physical_iot_integration_plan.md`
- `docs/decisions/ADR-002-home-assistant-device-layer.md`
- `docs/development/2026-09-05-physical-iot-plan.md`
- `docs/README.md`

## Test Evidence

- `git diff --check` completed without whitespace errors.
- The Mac completion-sync helper completed a fetch, rebase onto an existing Windows-originated commit, and push to `origin/main` successfully.
- No hardware, VM, Matter, ZHA, or mains-wiring test was performed in this documentation task.

## Remaining Issues

- Exact device models, firmware versions, network configuration, and Home Assistant entity IDs are not yet recorded.
- VM hypervisor availability and USB passthrough behavior for ZBDongle-E are not yet verified.
- Matter feature exposure for each Aqara device is not yet verified.

## Next Step

Install Home Assistant OS on the MacBook VM and confirm browser access before pairing the Aqara M3 Matter Bridge.
