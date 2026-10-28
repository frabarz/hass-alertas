# Configuration

Setup is entirely in the Home Assistant UI: **Settings → Devices & Services →
Add Integration → Alertas Chile**. There is nothing to enter; the flow checks
the relay handshake and creates a single entry. The integration deliberately
allows only one entry per Home Assistant instance.

## Sources

| Source | Key | Payload highlights |
| --- | --- | --- |
| Centro Sismológico Nacional | `csn` | `magnitud`, `tipo`, `lugar`, `profundidad`, `fecha` |
| Sismo Detector | `sismo_detector` | `magnitud`, `tipo`, `lugar`, `hora`, `estado` |
| SENAPRED SAE | `senapred_sae` | `mensaje` |
| Tsunami (SHOA/SENAPRED) | `tsunami` | `estado`, `zonas`, `texto`, `revision`, `ts` |

Every payload carries an `active` flag. The relay pushes a message when the
state changes, including clears (`active: false`).

## Options

Open the integration card → **Configure** to choose which sources create
entities:

- **All sources** (default) creates four binary sensors plus the summaries.
- Unchecking a source removes only its binary sensor. The relay still
  delivers the message, and the summary sensors/event still reflect it.
- At least one source must remain selected.

Changing options reloads the entry so entities are added or removed cleanly.

## Push model

There is no polling interval. The integration keeps one WebSocket open with a
30-second heartbeat and reconnects with exponential backoff (5 s → 60 s).
After three consecutive failed reconnects it raises a persistent repair issue;
a successful reconnect dismisses it.

## Event bus

Each relay envelope also fires a Home Assistant bus event named
`alertas_chile_alert` with `source`, `source_name`, `active`, `received_at`,
and the raw `data` payload. Use the event entity for normal automations; the
bus event is available for advanced templates.
