# ADR-002: Home Assistant as the Physical Device Layer

## Status

Accepted and first adapter implemented

## Context

The project is moving from a virtual device simulator to a mixed physical environment. Aqara sensors and the curtain controller use an Aqara Hub M3, while SONOFF ZBMINIL2 relays are planned for a separate Zigbee coordinator. The FastAPI application must not depend on vendor-specific transport details.

## Decision

Use Home Assistant OS in a virtual machine on the MacBook as the physical-device abstraction layer.

- Aqara Hub M3: Matter Bridge to Home Assistant.
- Aqara child devices: connected to the M3 through Aqara Zigbee.
- SONOFF ZBMINIL2: connected through ZBDongle-E and ZHA.
- FastAPI: communicate only with Home Assistant's REST API after manual hardware acceptance testing succeeds.
- Existing `DeviceStore`: retained as the simulation path.

## Rationale

- One Home Assistant instance normalizes Matter and Zigbee devices behind entity IDs and services.
- The LLM command schema remains independent of Aqara, SONOFF, Matter, and Zigbee details.
- Hardware faults can be isolated before the LLM and FastAPI are introduced.
- Running the VM on the existing MacBook avoids adding a second computer during development.

## Consequences

- The MacBook must remain awake while the physical system is being demonstrated or tested.
- Actual HA entity IDs and supported features must be discovered and recorded; they cannot be assumed from device names.
- The first implementation maps only `cover.living_room_curtain` to the confirmed HA entity `cover.aqara_curtain_controller`, and only supports open, close, and stop.
- Other virtual-device commands are rejected in the physical backend until their real HA entity IDs and services have been verified.
- SONOFF/ZBDongle-E/ZHA work is deferred because the relay installation cannot currently be performed.
