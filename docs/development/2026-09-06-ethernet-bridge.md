# Ethernet Bridge Alignment

Date: 2026-09-06

## Objective

Place Home Assistant on the local network segment containing Aqara Hub M3 and complete Matter Bridge commissioning without altering the household router configuration.

## Work Completed

- Stopped the Home Assistant VM and changed its bridged network attachment to the active wired adapter.
- Restarted the VM and confirmed Home Assistant and the user-identified Hub M3 were reachable.
- Confirmed the VM had both local IPv4 and IPv6 connectivity.
- Reproduced a dashboard reachability difference between the MacBook's active network paths.
- Added the temporary `tools/ha-dashboard-relay.py` diagnostic path and ADR-004.
- Determined that the commissioning phone initially occupied a different routed household network segment.
- Joined the phone to the same local segment as Home Assistant and Hub M3 for commissioning.
- Completed M3 Matter Bridge commissioning.
- Invoked a Home Assistant cover service and verified the physical curtain closed.

Public documentation intentionally omits the actual addresses, interface names, VM hardware address, router models, firmware, and household routing topology.

## Verification Evidence

- VM status and address discovery completed successfully.
- Ping to the user-identified M3 address returned 2/2 packets.
- Home Assistant dashboard returned HTTP 200.
- The temporary relay returned HTTP 200 and a WebSocket upgrade returned 101.
- The user confirmed the Home Assistant login screen appeared on the iPhone through the relay.
- User-provided Home Assistant pages showed Aqara Hub M3 and the bridged curtain, illuminance, and temperature/humidity devices.
- Matter Server accepted the curtain close command and reported success.
- Home Assistant reported the curtain closed at position 0.
- The user directly observed the physical curtain close.

## Technical Conclusion

HTTP reachability and a dashboard relay do not provide Matter discovery. Matter commissioning requires the phone, controller, and bridge to have suitable local IPv6 and mDNS multicast communication. The successful commissioning session placed those participants on one local network segment and used a fresh M3 pairing code.

## Modified Files

- `docs/architecture/home-assistant-network.md`
- `docs/decisions/ADR-004-temporary-ha-dashboard-relay.md`
- `docs/development/2026-09-06-ethernet-bridge.md`
- `docs/hardware/inventory.md`
- `docs/troubleshooting/ha-iphone-network.md`
- `tools/ha-dashboard-relay.py`

## Remaining Scope

Motion sensing is excluded from the current MVP. SONOFF relay work remains deferred because physical installation was not available.
