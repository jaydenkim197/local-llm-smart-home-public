# ADR-005: Request-Time Home Context

## Status

Accepted and implemented for Context-Aware Control v1

## Context

The local LLM previously received only the user request and a static device catalog. Home Assistant now exposes live Aqara temperature, humidity, illuminance, occupancy, and curtain state. The system needs current state for context-dependent decisions without coupling prompts to Aqara entity IDs or introducing an event-cache subsystem prematurely.

## Decision

- Read one Home Assistant `/api/states` snapshot at the beginning of every text or audio command request.
- Normalize selected Aqara states into a vendor-neutral living-room context.
- Include raw values and deterministic derived flags in the LLM input.
- Pass the physical actuator allow-list separately; sensors are read-only.
- Apply a deterministic policy after LLM parsing to remove redundant curtain actions and protect the initial dark/bright behavior.
- Keep the simulation backend and produce an equivalent simulated context.

Initial thresholds are 100 lx for dark, 800 lx for bright, 28 C for hot, and 65% for humid. They are configuration candidates, not universal comfort claims.

## Consequences

- Each request makes one additional HA REST call before inference.
- The context is fresh at request time but is not a continuous event stream.
- Vendor entity IDs remain inside the integration layer.
- The LLM can inspect unsupported conditions such as heat but cannot actuate an unmapped air conditioner.
- WebSocket state caching and autonomous event-triggered control remain future milestones.
