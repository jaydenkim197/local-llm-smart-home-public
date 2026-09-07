# M3 IR Air Conditioner Matter Diagnosis

## Objective

Determine whether the Aqara Hub M3 IR Air Conditioning Controller is available to the project as a physical Home Assistant climate actuator.

## Work Completed

- Queried all active Home Assistant states and found no `climate.*` entity.
- Queried the HA entity registry and found no active or disabled climate entity.
- Confirmed the M3 Matter node is available, is a bridge, and has an active Home Assistant fabric.
- Listed M3 bridged child devices from the HA registry: light sensor endpoint 2, temperature/humidity sensor endpoint 3, and curtain controller endpoint 8.
- Reloaded the Matter config entry and performed `matter/interview_node` on the M3 without deleting the fabric or resetting the hub.
- Rechecked HA state after each operation; no AC endpoint or climate entity appeared.
- The user subsequently reported adding IR AC scenes to Aqara Advanced Matter Bridging Scene Sync. A Matter WebSocket re-interview for the M3 completed successfully. After a 70-second wait, the HA Matter entity/device registries still contained only the original M3, curtain, light-detection, and temperature/humidity endpoints. No Scene Sync virtual plug or switch was created.

## Result

The IR AC is present in Aqara Home but is not currently exposed through the M3 Matter bridge to Home Assistant, either directly as a climate endpoint or indirectly as a synchronized scene actuator. No physical AC mapping was added to the repository because no target HA entity exists.

## Next Step

In Aqara Home, confirm that both AC scenes are enabled in the M3's Scene and Signal Sync list, then re-interview the M3 from its Home Assistant Matter device page. Once HA creates a `switch.*` or plug-like scene endpoint, inspect its actual service behavior before mapping it to `climate.air_conditioner`.
