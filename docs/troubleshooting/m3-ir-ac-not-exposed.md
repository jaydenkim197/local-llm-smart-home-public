# Aqara M3 IR AC Not Exposed to Home Assistant

## Symptom

The Aqara Home app can control the Hub M3 IR Air Conditioning Controller, but Home Assistant has no `climate.*` entity for it.

## Confirmed Environment Evidence

- The M3 Matter node is available as node 3 and is connected to the Home Assistant fabric.
- The Matter config entry is loaded.
- The node-level diagnostic reports a bridge on Ethernet with IPv6 and IPv4 addresses.
- The HA device registry lists only the M3's bridged child endpoints for the light sensor, temperature/humidity sensor, and curtain controller.
- No bridged child device or active/disabled entity with a climate, thermostat, air-conditioner, or HVAC identity was found.
- `homeassistant.reload_config_entry` for Matter and `matter/interview_node` both completed successfully, but did not add an AC entity.
- After the user reported adding IR AC scenes to Aqara Advanced Matter Bridging Scene Sync, a second `matter/interview_node` request completed successfully. After 70 seconds, the HA Matter registry still listed only the existing sensor and curtain endpoints; no virtual plug, switch, scene, or AC endpoint had appeared.

## Interpretation

The M3 does not expose the IR AC as a usable Matter thermostat. However, after Scene Sync was correctly enabled, Home Assistant discovered virtual Matter outlet switches for the fixed `AC Cool 24` and `AC Off` commands. The project maps those two command triggers to the logical air-conditioner interface without claiming a physical AC state.

## Scene Sync Check

The fallback path is Aqara Advanced Matter Bridging Scene Sync. It should publish separate virtual plug or switch endpoints for an `AC Cool 24` scene and an `AC Off` scene. They must be visible in the Aqara Matter sync list as enabled before Home Assistant can discover them.

After confirming both entries are enabled in Aqara Home, use the Home Assistant Matter device page's re-interview control. A successful result is a new `switch.*` or plug-like entity in HA. In this installation, that result was `AC Cool 24` and `AC Off`. Do not treat either switch state as the actual IR AC state.

These virtual switches act as momentary triggers. A single `switch.turn_on` was accepted by HA but did not physically operate the AC during the first project test. A one-second reset interval also produced an HA `on` transition without a physical response during browser microphone acceptance. Sending `switch.turn_off`, waiting two seconds, and then sending `switch.turn_on` physically ran the scene in the direct experiment. The switch automatically returned to `off` about five seconds later. Use the verified two-second reset-and-trigger sequence for every preset invocation and never interpret the temporary switch state as AC feedback.

For cooling startup in this installation, triggering the Cool 24 virtual switch alone remained physically unreliable. The selected sequence is to trigger the actual `AC Off` Scene first, wait, and then trigger the `AC Cool 24` Scene. This sends an appliance Off IR command before the Cool 24 IR command; it is distinct from merely resetting the Cool switch's virtual state.

## Aqara-Side Check

In Aqara Home, verify that the IR AC is not only controllable in the app but is configured as a Matter-shareable accessory of the M3. For IR AC thermostat behavior, verify that the M3 IR AC configuration uses the installed Aqara Temperature/Humidity Sensor T1 as its temperature source or climate sensor, where the app offers that setting. The M3 supports bridging one IR AC to Matter, but the vendor notes that platform behavior can vary.

After this linkage is confirmed, check whether the M3's third-party Matter ecosystem view shows the AC among the bridged accessories. Then rerun the Home Assistant Matter re-interview; do not reset the M3 or remove the current Matter fabric.

## Source

- [Aqara Hub M3 IR AC Matter Bridge announcement](https://www.aqara.com/en/news/aqara-releases-hub-m3-to-global-markets/)
