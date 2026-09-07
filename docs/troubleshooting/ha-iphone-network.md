# iPhone Cannot Reach the Home Assistant VM

## Symptom

Home Assistant is reachable from the MacBook through one local interface, while an iPhone connected through another household network segment cannot open the dashboard.

## Diagnosis

1. Confirm Home Assistant is running and reachable from the MacBook.
2. Compare the phone and VM network segments without recording their actual addresses in public notes.
3. Check client isolation, routed boundaries, firewall rules, and multicast behavior.
4. Do not assume HTTP routing proves Matter readiness. Matter commissioning also needs local IPv6 and mDNS multicast.

## Temporary Dashboard Relay

`tools/ha-dashboard-relay.py` can forward Home Assistant HTTP/WebSocket traffic for a controlled diagnostic session. Supply bind, target, and allowed-network values through local command arguments only. Keep Home Assistant authentication enabled and stop the relay after use.

This relay does not forward Matter discovery traffic.

## Matter Resolution

For the successful commissioning attempt, the iPhone, Home Assistant VM, and Hub M3 were placed on the same local network segment. A fresh pairing code was then generated and used immediately. No hub reset, sensor re-pairing, or household router reconfiguration was required.

Matter requirements: https://www.home-assistant.io/integrations/matter/
