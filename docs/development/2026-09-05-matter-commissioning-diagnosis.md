# Development Log: Aqara M3 Matter Commissioning Diagnosis

Date: 2026-09-05

## Objective

Diagnose the failed attempt to add Aqara Hub M3 as a Matter bridge without resetting the hub, changing Aqara Zigbee pairings, or changing household router configuration.

## Work Completed

- Confirmed the Home Assistant OS VM was running and reachable.
- Collected Home Assistant network status and Matter Server logs.
- Confirmed the Matter Server app was installed and started.
- Checked Home Assistant host listeners.
- Attempted a read-only mDNS packet capture; the required capture utility was not present in HA OS.
- Compared the MacBook's active local network paths.

## Observed Evidence

- The HA VM had working IPv4 connectivity and a local IPv6 address.
- Matter Server reported a healthy startup, mDNS publication, and active WebSocket listeners.
- The failed attempt logged: `Commission failed: discovery of node with discriminator 12 failed: No commissionable device was discovered`.
- A later discovery attempt also lacked a successful commissioning event in the captured window.
- HTTP reachability succeeded, but that alone did not prove same-segment IPv6 and multicast reachability.
- The MacBook had active network paths in different local broadcast domains.

Public documentation intentionally omits addresses, interface names, hardware addresses, router models, and internal routing topology.

## Modified Files

- `docs/development/2026-09-05-matter-commissioning-diagnosis.md`

## Test Evidence

- VM status reported `started`.
- The Home Assistant dashboard returned its HTML document.
- Home Assistant CLI output and Matter Server logs were inspected in the VM console.

## Outcome

The failure was narrowed to Matter discovery conditions rather than a stopped Matter Server. A later session succeeded after the commissioning phone, Home Assistant VM, and Hub M3 were placed on the same suitable local network segment and a fresh pairing code was used. No hub reset or sensor re-pairing was required.
