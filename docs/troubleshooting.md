# Troubleshooting

## The setup form says the relay cannot be reached

Home Assistant could not complete the WebSocket handshake with
`wss://alertas.alertas-chile.fyi`.

- Confirm the host has outbound TLS/WebSocket access (port 443).
- Check DNS and any firewall/proxy that blocks WebSocket upgrades.
- The relay may be down; retry later.

## Entities stopped updating

Check `binary_sensor.connection`:

- **off** — the WebSocket is reconnecting. The integration retries every
  5 s, doubling up to 60 s. Existing sensor states remain as last known.
- **on** — connected. Use `sensor.last_message` to see when the last envelope
  arrived. A quiet feed simply has no new alerts.

After three failed reconnects Home Assistant shows a **Alertas Chile relay
unreachable** repair issue. Confirm the repair to reload the entry and retry.
The issue disappears automatically on a successful reconnect.

## A source is missing

Open the integration card → **Configure** and check that the source is
selected. Disabling a source removes only its binary sensor; summary sensors
and the event entity continue to work.

## Alert says “preliminar”

Sismo Detector and CSN may publish preliminary information first and update it
later. Treat preliminary magnitudes as provisional and follow official
channels.

## I restarted Home Assistant; why did I get no historical alerts?

The relay is a live push feed. After a restart the integration reconnects and
reports the current active state, but it does not backfill past messages.

## The integration created one entry and refuses another

This is intentional. Alertas Chile is a single feed per Home Assistant
instance; all sources are configured in the options flow.

## Still stuck

Enable debug logging and reload the integration:

```yaml
logger:
  default: warning
  logs:
    custom_components.alertas_chile: debug
```

Then inspect **Settings → System → Logs** for `Alertas Chile relay error`
messages.
