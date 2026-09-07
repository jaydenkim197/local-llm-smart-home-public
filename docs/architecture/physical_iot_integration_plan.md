# Local LLM Smart Home — Physical IoT Integration Plan

**Project:** A Fully Local Natural Language-Based IoT Control System Using LLM  
**Team:** ICNI  
**Current stage:** Context-Aware physical demonstration MVP completed and filmed

**Immediate milestone:**

Preserve the completed filmed MVP. Autonomous control experiments and edge-device migration are separate future milestones.

**Scope note:** This document describes the target architecture and original bring-up workflow. Current implementation is recorded in `system_overview.md`. Device models, entity IDs, and test outcomes become factual only after they are recorded in the hardware inventory and development logs. SONOFF, ZBDongle-E, and ZHA remain future architecture but are excluded from the active phase because physical installation is not currently possible.

---

## 1. Target System Architecture

### 1.1 Overall Architecture

```text
User Voice / Text
        ↓
faster-whisper
        ↓
FastAPI
        ↓
Local LLM (Ollama)
        ↓
Validated JSON Command
        ↓
Command Router
        ↓
HomeAssistantAdapter
        ↓
Home Assistant
      /               \
 Matter                 Zigbee
   ↓                       ↓
Aqara Hub M3          ZBDongle-E
   ↓ Zigbee                ↓ Zigbee
Aqara Sensors /        SONOFF ZBMINIL2
Curtain Controller         ↓
                           LED Lights
```

### 1.2 MacBook Server Role

```text
MacBook Air M1 8GB
│
├─ macOS
│  ├─ FastAPI
│  ├─ Ollama
│  ├─ faster-whisper
│  └─ Existing Web UI
│
└─ VM
   └─ Home Assistant OS
      ├─ Matter Server
      └─ ZHA
```

The MacBook is the central local server.

- STT runs locally.
- LLM inference runs locally.
- FastAPI handles user commands and routing.
- Home Assistant manages real devices.
- Aqara M3 bridges Aqara Zigbee devices to Home Assistant through Matter.
- ZBDongle-E directly coordinates general Zigbee devices such as SONOFF ZBMINIL2.

---

## 2. Device Integration Paths

### 2.1 Aqara Devices

```text
Aqara Sensors / Curtain
        ↓ Zigbee
Aqara Hub M3
        ↓ Matter Bridge
Home Assistant
        ↓
FastAPI / Local LLM
```

Target Aqara devices:

- Aqara Motion Sensor T1 ×2
- Aqara Illuminance Sensor T1 ×2
- Aqara Temperature/Humidity Sensor T1 ×1
- Aqara Smart Curtain Controller ×1

### 2.2 SONOFF Lighting

```text
Wall Switch
   ↓
SONOFF ZBMINIL2
   ↓ Zigbee
ZBDongle-E
   ↓
ZHA
   ↓
Home Assistant
   ↓
FastAPI / Local LLM
```

Initial installation priority:

1. Bathroom
2. Study
3. Kitchen
4. Remaining rooms if time permits

---

## 3. Design Principles

### 3.1 Home Assistant Is the Device Abstraction Layer

FastAPI must not directly control Aqara or SONOFF devices.

```text
FastAPI
   ↓
Home Assistant API
   ↓
HA Entity / Service
   ↓
Matter or Zigbee
   ↓
Physical Device
```

Benefits:

- Vendor-specific protocols are hidden below Home Assistant.
- LLM / FastAPI do not need to know whether a device is Matter, Zigbee, IR, or Wi-Fi.
- Device replacement does not require redesigning the LLM command format.

---

### 3.2 Keep Simulation Mode

The existing `DeviceStore` must not be removed.

```text
Command Router
      │
      ├─ SimulationAdapter
      │    └─ DeviceStore
      │
      └─ HomeAssistantAdapter
           └─ Real Home Assistant
```

This allows:

- LLM testing without physical hardware
- debugging when a real device is offline
- regression testing
- controlled experiments

---

### 3.3 Separate Hardware Bring-Up From LLM Integration

Do not debug the entire pipeline at once.

Correct order:

```text
Physical Device
→ Home Assistant
→ Manual HA Control
→ HomeAssistantAdapter
→ FastAPI
→ LLM
→ STT
```

This isolates failures by layer.

---

## 4. Immediate Success Criteria

The first hardware-integration session is successful when the MacBook can do all of the following through Home Assistant:

### Home Assistant

- Home Assistant OS VM is accessible from a browser.
- The VM has a LAN-reachable IP address through bridged networking.

### Aqara M3 Matter Bridge

- The M3 is paired to Home Assistant as a Matter bridge.
- At least one Aqara sensor is visible in Home Assistant.
- The curtain is visible in Home Assistant and can be opened or closed.

### Deferred Milestone

SONOFF relay installation and multi-room lighting verification are separate later phases. They are not prerequisites for the first Matter-bridge checkpoint.

---

## 5. Physical MVP Success Criteria

The physical MVP is complete only when Home Assistant can perform all of the following before FastAPI or the LLM is connected:

### Aqara Devices

- Read temperature, humidity, illuminance, and motion state where exposed by Matter.
- Read curtain state.
- Open, close, and stop the curtain when those features are exposed.

### SONOFF Lighting

For the following initial rooms:

- Bathroom
- Study
- Kitchen

The system must:

- Read ON/OFF state
- Turn the light ON from Home Assistant
- Turn the light OFF from Home Assistant
- Reflect physical wall-switch changes back into Home Assistant

---

# 6. Development Workflow

```text
Phase 0
Environment preparation
        ↓
Phase 1
Aqara device setup
        ↓
Phase 2
Home Assistant OS VM setup
        ↓
Phase 3
Aqara M3 → Matter → Home Assistant
        ↓
Phase 4
Aqara entity inventory and manual verification
        ↓
Phase 5
SONOFF physical installation
        ↓
Phase 6
ZBDongle-E → ZHA
        ↓
Phase 7
SONOFF ZBMINIL2 → ZHA
        ↓
Phase 8
Final entity inventory and manual acceptance test
        ↓
Phase 9
Local/offline verification
        ↓
Phase 10
GitHub documentation
        ↓
Next Development Stage
HomeAssistantAdapter
        ↓
FastAPI → HA
        ↓
LLM → Real Devices
```

---

# 7. Phase-by-Phase Plan

## Phase 0 — Environment Preparation

### Objective

Prepare a stable local network and label all devices.

### Recommended Network Layout

```text
Home Router
├─ Ethernet or Wi-Fi → MacBook
├─ Ethernet → Aqara M3
└─ Wi-Fi    → iPhone
```

All devices must use the same normal LAN.

Avoid:

- Guest Wi-Fi
- Separate VLANs
- AP isolation
- different subnets during initial setup

### Device Labels

Before pairing, label physical devices.

Example:

```text
SONOFF-01 = Bathroom
SONOFF-02 = Study
SONOFF-03 = Kitchen

AQ-MOTION-01
AQ-MOTION-02

AQ-LUX-01
AQ-LUX-02

AQ-TEMP-01

AQ-CURTAIN-01
```

### Completion Condition

- MacBook, M3, iPhone are connected to the same LAN.
- All physical devices can be uniquely identified.

---

## Phase 1 — Aqara Device Setup

### Objective

Make all Aqara devices work normally inside Aqara Home before involving Home Assistant.

### Pairing Order

```text
Aqara Hub M3
      ↓
Temperature/Humidity Sensor T1
      ↓
Illuminance Sensor T1 #1
      ↓
Illuminance Sensor T1 #2
      ↓
Motion Sensor T1 #1
      ↓
Motion Sensor T1 #2
      ↓
Curtain Controller
```

### Sensor Verification

#### Temperature/Humidity

Check:

- temperature value
- humidity value
- value changes over time

#### Illuminance

Test:

```text
normal light
→ cover sensor
→ lux value decreases
```

#### Motion

Test:

```text
no motion
→ move in front of sensor
→ motion detected
```

#### Curtain

Verify:

- OPEN
- CLOSE
- STOP
- travel range calibration

Curtain travel calibration must be completed before Home Assistant integration.

### Completion Condition

In Aqara Home:

- Temperature/Humidity sensor works
- Both illuminance sensors work
- Both motion sensors work
- Curtain opens and closes correctly

---

## Phase 2 — Home Assistant OS VM Setup

### Objective

Run Home Assistant OS on the MacBook as the local device gateway.

### Initial Resource Allocation

Recommended starting point:

```text
CPU: 2 vCPU
RAM: 2 GB
Disk: sufficient HA OS virtual disk
```

Keep memory allocation conservative because the MacBook must also run:

- Ollama
- faster-whisper
- FastAPI
- macOS

### VM Network

Use:

```text
Bridged Networking
```

Do not use NAT for the final setup.

The HA VM should receive its own IP address from the home router.

Example:

```text
MacBook            192.168.x.20
Home Assistant VM  192.168.x.30
Aqara M3           192.168.x.40
```

### Completion Condition

Home Assistant dashboard is accessible from the MacBook through:

```text
http://homeassistant.local:8123
```

or:

```text
http://<HA-IP>:8123
```

---

## Phase 3 — Aqara M3 Matter Bridge Integration

### Objective

Expose Aqara Zigbee devices to Home Assistant through the M3 Matter Bridge.

### Logical Path

```text
Aqara Devices
    ↓ Zigbee
Aqara Hub M3
    ↓ Matter Bridge
Home Assistant
```

### Steps

1. Install/enable Matter support in Home Assistant OS.
2. Open Aqara Home.
3. Open M3 Matter Bridge settings.
4. Obtain the Matter pairing code.
5. Add the M3 to Home Assistant as a Matter device.
6. Wait for bridged child devices to appear.

### Expected Home Assistant Entity Types

Examples:

```text
cover.*
sensor.*temperature*
sensor.*humidity*
sensor.*illuminance*
binary_sensor.*motion*
```

Exact entity IDs must be recorded from the real Home Assistant instance.

### Important Verification

Do not assume every Aqara feature exposed in Aqara Home will appear through Matter.

For each device, verify what Home Assistant actually receives.

### Completion Condition

From Home Assistant:

- curtain can be controlled
- temperature can be read
- humidity can be read
- illuminance can be read
- motion state can be read

---

## Phase 4 — Aqara Entity Inventory and Manual Verification

### Objective

Record the actual Home Assistant entities exposed by the M3 Matter Bridge and verify them manually before adding SONOFF hardware.

### Required Record

For every Aqara device exposed in Home Assistant, record the physical label, model, actual HA entity ID, state fields, and supported actions in `docs/hardware/inventory.md`.

### Completion Condition

- At least one sensor state changes in Home Assistant when the physical environment changes.
- The curtain responds to Home Assistant controls.
- The actual Matter feature exposure is known before adapter design begins.

---

## Phase 5 — SONOFF Physical Installation

### Objective

Install SONOFF ZBMINIL2 behind selected wall switches only after Aqara Matter verification has established a working Home Assistant baseline.

### Installation Priority

1. Bathroom
2. Study
3. Kitchen
4. Remaining rooms if time remains

### Known Conditions

- LED lighting
- no neutral wire at wall switch
- approximately two wires at each switch
- ZBMINIL2 chosen because it supports no-neutral installation

### Important Electrical Safety

Do not assume wiring solely from wire count or wire color.

Before installation:

- shut off the circuit breaker
- verify absence of voltage
- identify the actual line/load configuration
- verify the circuit is compatible with the manufacturer wiring diagram
- do not proceed if the switch is part of an unknown multi-way circuit
- verify bathroom circuits do not combine lighting and another load unexpectedly

Mains wiring should be performed by a qualified person in accordance with local electrical requirements and the manufacturer's installation instructions.

### After Installation

Before Zigbee pairing, confirm physical operation:

```text
Wall switch ON  → Light ON
Wall switch OFF → Light OFF
```

### Completion Condition

Bathroom, study, and kitchen lights still operate normally from their wall switches after relay installation.

---

## Phase 6 — ZBDongle-E + ZHA Setup

### Objective

Create a direct Zigbee network in Home Assistant for SONOFF devices.

### Logical Path

```text
ZBDongle-E
    ↓ USB passthrough
Home Assistant OS VM
    ↓
ZHA
```

### Steps

1. Connect ZBDongle-E to the MacBook.
2. Pass the USB device through to the HA OS VM.
3. Confirm Home Assistant detects the serial device.
4. Add Zigbee Home Automation (ZHA).
5. Select the ZBDongle-E as the coordinator.

### Why ZHA First

ZHA is preferred for initial bring-up because it:

- runs directly inside Home Assistant
- requires fewer components
- is easier to debug during first integration

Zigbee2MQTT can be evaluated later if needed.

### Completion Condition

Home Assistant shows a working ZHA Zigbee coordinator.

---

## Phase 7 — SONOFF ZBMINIL2 Pairing

### Objective

Pair each installed relay to the ZBDongle-E network.

### Pair One Device at a Time

Order:

```text
SONOFF-01 Bathroom
        ↓
SONOFF-02 Study
        ↓
SONOFF-03 Kitchen
```

Do not put multiple relays into pairing mode simultaneously.

### After Pairing

Rename the entities immediately.

Suggested visible names:

```text
Bathroom Light
Study Light
Kitchen Light
```

The actual Home Assistant entity domain may be `switch.*` or `light.*`. Record the discovered entity ID rather than assuming one.

### Per-Relay Test

For each relay:

1. Home Assistant → ON → physical LED turns ON
2. Home Assistant → OFF → physical LED turns OFF
3. Wall switch → physical LED changes normally
4. Home Assistant state updates to match the real light state

### Completion Condition

At least bathroom, study, and kitchen lights can be read and controlled from Home Assistant.

---

## Phase 8 — Final Home Assistant Entity Inventory and Manual Acceptance Test

### Objective

Create the canonical mapping between real devices and Home Assistant entities.

### Example Logical Inventory

```text
cover.living_room_curtain

sensor.living_room_temperature
sensor.living_room_humidity

sensor.living_room_illuminance_1
sensor.living_room_illuminance_2

binary_sensor.living_room_motion_1
binary_sensor.living_room_motion_2

light.bathroom_main
light.study_main
light.kitchen_main
```

These are project-level logical IDs. Map them to the actual `switch.*` or `light.*` entity IDs recorded in Home Assistant.

### Also Configure Areas

Examples:

```text
Living Room
Bathroom
Study
Kitchen
```

### Record Per Device

For every device record:

- physical device name
- model
- room
- gateway/coordinator
- protocol
- HA device name
- HA entity ID
- supported actions
- observed state fields
- integration test result

### Completion Condition

Every integrated physical device has an unambiguous HA entity mapping.

---

### Sensor Tests

From the MacBook Home Assistant dashboard:

- read current temperature
- read humidity
- observe illuminance changes
- observe motion-state changes

### Curtain Tests

From Home Assistant:

```text
OPEN
CLOSE
STOP
```

Verify real movement.

### Lighting Tests

From Home Assistant:

- Bathroom ON/OFF
- Study ON/OFF
- Kitchen ON/OFF

Then operate the wall switch and confirm HA reflects the resulting state.

### Completion Condition

The MacBook can monitor and control all target physical devices through Home Assistant without the FastAPI/LLM layer.

---

## Phase 9 — Local / Offline Verification

### Objective

Verify the core smart-home control path works without external internet access.

### Test

Keep the LAN active but disconnect WAN internet.

Expected local paths:

```text
MacBook ↔ Home Assistant ↔ M3 ↔ Aqara Devices

MacBook ↔ Home Assistant ↔ ZBDongle-E ↔ SONOFF
```

Verify:

- curtain control
- sensor readings
- SONOFF light control

### Completion Condition

Core smart-home control continues operating inside the local LAN.

---

## Phase 10 — GitHub Documentation

Repository:

```text
{GITHUB_USER}/local-llm-smart-home
```

### Update

```text
docs/hardware/inventory.md
```

Record:

- actual device model
- protocol
- gateway
- HA entity ID
- test result

### Add Development Log

Example:

```text
docs/development/2026-09-05-physical-iot-integration.md
```

Include:

- objective
- work completed
- files modified
- actual test evidence
- unresolved issues
- next step

### Architecture Update

After successful physical integration, update:

```text
docs/architecture/system_overview.md
```

The architecture should evolve from:

```text
Command Router
→ Virtual DeviceStore
```

to:

```text
Command Router
├─ SimulationAdapter
│  └─ DeviceStore
│
└─ HomeAssistantAdapter
   └─ Home Assistant
```

---

# 8. Next Development Stage After Hardware Integration

Do not begin this until the physical MVP success criteria and Phase 8 manual acceptance test succeed.

## HomeAssistantAdapter

Target structure:

```text
Validated JSON
      ↓
Command Router
      ↓
HomeAssistantAdapter
      ↓
Home Assistant REST / WebSocket API
      ↓
HA Entity / Service
      ↓
Physical Device
```

### Example

LLM-side command:

```json
{
  "entity_id": "cover.living_room_curtain",
  "action": "close_cover"
}
```

Adapter translates it into the correct Home Assistant service call.

The LLM remains independent of Matter/Zigbee implementation details.

---

# 9. Physical MVP Milestone

The hardware integration session is complete when:

```text
MacBook
  ↓
Home Assistant
  ↓
├─ Aqara M3 / Matter
│  ├─ Curtain
│  ├─ Temperature
│  ├─ Humidity
│  ├─ Illuminance
│  └─ Motion
│
└─ ZBDongle-E / ZHA
   ├─ Bathroom Light
   ├─ Study Light
   └─ Kitchen Light
```

and all target states can be read and controllable devices can be operated from the MacBook.

At that point the next software task is:

```text
HomeAssistantAdapter
        ↓
FastAPI
        ↓
Local LLM
        ↓
Speech/Text → Real Home
```

---

# 10. Recommended Execution Order

```text
1. Connect MacBook + M3 to the same LAN
2. Label all devices
3. Pair Aqara sensors and curtain with M3
4. Verify all Aqara functions in Aqara Home
5. Install Home Assistant OS VM on MacBook
6. Configure bridged networking
7. Add Matter support
8. Pair M3 Matter Bridge with Home Assistant
9. Record and verify Aqara entities in Home Assistant
10. Install one SONOFF relay with qualified electrical assistance and verify wall-switch operation
11. Connect ZBDongle-E to the HA VM and configure ZHA
12. Pair the verified SONOFF relay, then repeat one device at a time
13. Rename and organize entities; record actual entity IDs
14. Perform full manual acceptance test
15. Perform optional offline test only after online-LAN testing is complete
16. Update GitHub documentation
```

---

## Current Implemented Checkpoint

- Home Assistant OS, Matter Server, Aqara M3 bridge, Aqara sensors, and curtain are operational.
- FastAPI and the local LLM have controlled the actual curtain through `HomeAssistantAdapter`.
- Request-time HA state collection supplies temperature, humidity, illuminance, and curtain state to the LLM, with local solar and cached outdoor context.
- Physical execution includes the mapped curtain and command-only Aqara M3 IR AC scenes. Browser microphone acceptance and the final demonstration recording are complete.
- Motion and SONOFF-related phases are deferred outside this MVP.

The active demonstration milestone is complete. Autonomous control or edge-device migration begins only as a separately scoped phase; the historical SONOFF sequence resumes only when physical installation becomes possible.
