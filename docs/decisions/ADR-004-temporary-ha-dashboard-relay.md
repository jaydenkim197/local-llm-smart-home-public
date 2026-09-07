# ADR-004: Temporary HA Dashboard Relay

## Status

Accepted as a temporary diagnostic tool; not part of Matter commissioning.

## Context

The Home Assistant dashboard was reachable from the MacBook on the Matter LAN but not from an iPhone on a separate household network segment. Public records intentionally omit the addresses, interface names, router models, and internal routing topology involved.

## Decision

Use the standard-library Python relay in `tools/ha-dashboard-relay.py` for temporary authenticated dashboard HTTP/WebSocket access. Bind and target addresses must be supplied locally and must never be committed. Restrict the relay to the required local client network, keep it session-scoped, and do not log payloads or credentials.

## Consequences

- The relay can provide temporary dashboard access without changing Home Assistant authentication.
- It does not carry Matter IPv6 or mDNS discovery and cannot solve Matter commissioning by itself.
- Matter commissioning must place the phone, Home Assistant, and Hub M3 on the same suitable local network segment.
- The relay should remain off unless needed for a controlled diagnostic session.
