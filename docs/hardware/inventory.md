# Hardware Inventory and Integration Status

## Recording Rule

Complete the fields below using the device label, packaging, manual, or vendor application before implementation. Do not infer the protocol from the device category.

## Home Assistant Development Host

| Component | Configuration | Verification |
| --- | --- | --- |
| MacBook development host | Apple Silicon M1, 8 GB memory | User-provided environment information |
| Hypervisor | UTM 4.7.5, QEMU ARM64 VM | VM created and started on 2026-09-05 |
| Home Assistant OS | 18.2, 2 vCPU, 2 GB RAM | HA CLI reported Home Assistant OS 18.2 |
| VM network | UTM Bridged Network on the Matter LAN | 2026-09-06: dashboard HTTP 200 and Matter commissioning verified; local identifiers omitted |

## Device Inventory

| Device | Model / Vendor | Control method | Local API or gateway | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Living room dimmable main light | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Living room smart bulb 1 | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Living room smart bulb 2 | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Aqara Hub M3 | Aqara Hub M3 (2051), firmware 4.3.6 | Ethernet, Aqara Zigbee, Matter Bridge | Home Assistant Matter integration | Commissioned | HA device page shown by user on 2026-09-06 |
| Living room curtain | Aqara Curtain Controller | Aqara Zigbee through Hub M3 | Matter Bridge to Home Assistant | Demo MVP physical acceptance complete | User observed browser microphone/context-aware curtain operation during final filming on 2026-09-06; prior FastAPI/LLM open and close tests were also completed. |
| Temperature sensor | Aqara Temp/Humidity Sensor T1 | Aqara Zigbee through Hub M3 | Matter Bridge to Home Assistant | Live state verified | HA REST returned `sensor.aqara_temp_humidity_sensor_t1_temperature`; observed 27.6 C and 27.88 C on 2026-09-06 |
| Humidity sensor | Aqara Temp/Humidity Sensor T1 | Aqara Zigbee through Hub M3 | Matter Bridge to Home Assistant | Live state verified | HA REST returned `sensor.aqara_temp_humidity_sensor_t1_humidity`; observed 48.3% and 48.21% on 2026-09-06 |
| Illuminance sensor | Aqara Light Detection Sensor T1 | Aqara Zigbee through Hub M3 | Matter Bridge to Home Assistant | Live state verified | HA REST returned `sensor.aqara_light_detection_sensor_t1_illuminance`; observed changing values from 1029.9 lx to 2686.6 lx on 2026-09-06 |
| Motion sensor | Aqara Motion Sensor T1 | Aqara Zigbee through Hub M3 | Matter Bridge to Home Assistant | Excluded from current MVP | Earlier HA state verification is preserved in the development history; the user removed this sensor from the current demo scope on 2026-09-06. |
| Air purifier | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Robot cleaner | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Smart TV | To be recorded | To be recorded | To be recorded | Not inspected | - |
| Air conditioner | Aqara Hub M3 IR Air Conditioning Controller | Hub M3 infrared control | Advanced Matter Bridging Scene Sync to Home Assistant | Demo MVP ON/OFF physical acceptance complete | Browser microphone input used live hot-room context and physically ran Off Scene followed by Cool 24. Standalone Off and a repeat sequence of Off twice then On were also physically observed on 2026-09-06. State feedback remains command-only. |
| Bedroom main lights | To be recorded | To be recorded | To be recorded | Not inspected | - |

## Per-Device Integration Record

Copy this section when starting each device.

### Device Name

- Date:
- Model and firmware:
- Vendor application tested:
- Network or transport: Wi-Fi / Bluetooth / Zigbee / IR / other
- Local control option:
- Required credentials or pairing method:
- Supported commands:
- Adapter module:
- Test command:
- Observed result:
- Remaining issue:
