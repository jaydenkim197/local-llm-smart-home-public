# ADR-003: UTM for the Home Assistant Development VM

## Status

Accepted for the current MacBook development environment

## Context

The project runs on an Apple Silicon MacBook Air (M1, 8 GB memory, 256 GB storage). The Home Assistant development instance must coexist with the local LLM, FastAPI service, and browser-based simulator without adding another computer.

## Decision

Run Home Assistant OS 18.2 in UTM 4.7.5 using a QEMU ARM64 virtual machine.

- Resources: 2 vCPU and 2 GB RAM.
- Disk: `haos_generic-aarch64-18.2.qcow2`.
- Initial network: UTM Shared Network for first-boot and host browser verification.
- Production-development network: UTM Bridged Network using the active home LAN interface before Matter pairing with Aqara Hub M3.

## Rationale

- UTM supports Apple Silicon and imported ARM64 QCOW2 disks without an administrator-password installation step.
- The selected allocation preserves headroom on an 8 GB MacBook for the local LLM and development tools.
- Shared networking provides an isolated first-boot path that can be verified from the MacBook before exposing the VM to the home LAN.

## Consequences

- The initial private UTM address was only used for first-boot verification.
- Bridged networking is verified and the VM has a LAN address from the home router.
- USB pass-through for ZBDongle-E remains a separate future verification item.
