# Development Log: Home Assistant OS VM First Boot

Date: 2026-09-05

## Objective

Create and boot the Home Assistant OS development VM on the M1 MacBook, then verify browser access from the host.

## Work Completed

- Installed UTM 4.7.5 in `{UTM_APP_PATH}`.
- Downloaded Home Assistant OS 18.2 ARM64 and imported `haos_generic-aarch64-18.2.qcow2`.
- Created the `Home Assistant OS` QEMU ARM64 VM with 2 vCPU and 2 GB RAM.
- Booted HA OS and observed the Home Assistant CLI and Supervisor startup screen.
- Verified that the VM received a local address on UTM Shared Network.
- Verified a Home Assistant HTTP response from the MacBook.
- Changed the stopped VM to UTM Bridged Network with the automatic active interface.
- Rebooted HA OS and observed a bridged LAN address.
- Verified a Home Assistant HTTP response through bridged networking.
- Completed the initial Home Assistant administrator account creation.
- Observed that the running Core later listened on host port `80`; verified the active dashboard URL.
- Restarted the stopped VM with `utmctl start 'Home Assistant OS'` and verified the active dashboard URL again.

## Modified Files

- `docs/decisions/ADR-003-utm-home-assistant-vm.md`
- `docs/development/2026-09-05-home-assistant-vm.md`
- `docs/hardware/inventory.md`

## Test Evidence

- Address discovery showed the VM on the expected local network; the actual IP and VM hardware address are omitted from public records.
- HTTP requests through both shared and bridged VM networking returned the Home Assistant HTML document during their respective tests.
- `ss -ltn` in the HA OS host shell later showed a listener on `0.0.0.0:80` and no listener on `8123`.
- A request to the active dashboard address returned the Home Assistant HTML document after VM restart.

## Remaining Issues

- Aqara M3 Matter Bridge pairing and entity discovery have not started.

## Next Step

Install the Matter integration and pair Aqara Hub M3 as a Matter bridge through the Home Assistant Companion App.
