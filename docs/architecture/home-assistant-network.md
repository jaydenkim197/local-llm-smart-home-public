# Current Home Assistant Network

Verified on 2026-09-06. Public documentation intentionally omits household addresses, interface identifiers, hardware addresses, router models, and internal routing topology.

## Implemented Configuration

- Home Assistant OS runs in an ARM64 VM with 2 vCPU and 2 GB RAM.
- The VM uses bridged networking on the LAN shared with Aqara Hub M3.
- Home Assistant and the Hub M3 are reachable from the MacBook on that LAN.
- Matter commissioning used an iPhone temporarily joined to the same local network segment.
- The VM retained local IPv6 and mDNS multicast connectivity required by Matter.

All addresses are DHCP-assigned and are stored only in private operational notes or local configuration, not in the public repository.

## Commissioning Constraint

Matter commissioning failed while the phone and Matter devices were separated by a routed household network boundary. Ordinary HTTP reachability was not sufficient because Matter commissioning also depends on local IPv6, mDNS multicast, and Bluetooth-assisted setup.

The successful procedure placed the iPhone, Home Assistant VM, and Hub M3 on the same local network segment for commissioning. No router reconfiguration, hub reset, or sensor re-pairing was required.

## Matter Bridge Result

- Aqara Hub M3 is visible in the Home Assistant Matter integration.
- HA lists Matter-bridged children for the curtain controller, illuminance sensor, and temperature/humidity sensor.
- Disabled hub diagnostic entities do not block the bridged device entities.
- End-to-end curtain control was verified: Home Assistant invoked the cover service, Matter Server returned success, HA reported the resulting position, and the user observed the curtain move physically.
- Motion sensing is excluded from the current MVP scope.

## Temporary Dashboard Access

A local TCP relay was used only to verify dashboard access from another household network segment. It preserved Home Assistant authentication and carried HTTP/WebSocket traffic, but it was not used for Matter discovery or commissioning. Public documentation omits its deployment addresses and household routing details.
