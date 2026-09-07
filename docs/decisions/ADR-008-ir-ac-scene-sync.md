# ADR-008: Aqara Scene Sync for IR Air Conditioner Control

## Status

Accepted and implemented

## Context

The Aqara Hub M3 IR Air Conditioning Controller is functional in Aqara Home but is not exposed to Home Assistant as a Matter `climate.*` entity. The M3's Advanced Matter Bridging Scene Sync exposes two fixed IR commands to Home Assistant as Matter outlet switches instead: `AC Cool 24` and `AC Off`.

## Decision

- Keep the vendor-neutral logical ID `climate.air_conditioner`.
- Map logical `turn_on` to an `AC Off` Scene followed by the configured `AC Cool 24` Matter Scene Sync switch. Map logical `turn_off` to the configured `AC Off` switch only.
- Invoke `switch.turn_off`, wait two seconds, and then invoke `switch.turn_on` for either scene. One-second reset attempts reached HA but did not produce a physical IR action during browser microphone acceptance; the direct two-second experiment did. Each switch is a momentary command trigger that requires a newly armed rising edge, not an AC state mirror.
- Permit no physical `set_temperature` or `set_mode` action through this adapter.
- Include AC scene-control availability in HomeContext, but represent the physical AC state as `unknown`.
- Mark every scene execution as command accepted rather than physically state-verified.
- Normalize user-facing confirmations to say the preset was sent, never that the AC state was confirmed.

## Consequences

- The local LLM can make a bounded cooling decision using current temperature, curtain position, solar, and outdoor context.
- The adapter does not claim that the AC is on, cooling, or at a measured target temperature after sending IR.
- Repeated requests retrigger the Aqara scene even if the virtual switch has not yet reset itself.
- Cooling startup sends a known Off IR command first, then sends the Cool 24 C IR command after a short interval.
- Direct climate feedback can be added later only if Aqara publishes a reliable Matter state endpoint or signal.
