# Home Assistant VM Troubleshooting

## Dashboard Address Refuses Connection on Port 8123

### Symptom

The configured Home Assistant dashboard URL on port `8123` returns a connection-refused error while the VM and Observer service are running.

### Observed Cause

On 2026-09-05, `ss -ltn` in HA OS showed the active Home Assistant listener on `0.0.0.0:80`, not `8123`.

### Resolution

Use the active local dashboard URL without an explicit port.

### Verification

An HTTP request to the active local dashboard URL returned the Home Assistant HTML document.

## Home Assistant VM Is Stopped

### Symptom

The LAN dashboard address times out and `utmctl status 'Home Assistant OS'` reports `stopped`.

### Resolution

Run:

```zsh
{UTM_APP_PATH}/Contents/MacOS/utmctl start 'Home Assistant OS'
```

Wait for the Home Assistant Core to finish starting, then open the active dashboard URL.

### Verification

On 2026-09-05, the VM dashboard became reachable after startup.
