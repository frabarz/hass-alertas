# Entities

All entities belong to one **Alertas Chile** device identified by the config
entry id.

## Binary sensors

| Entity | Device class | Meaning |
| --- | --- | --- |
| `binary_sensor.csn` | safety | CSN reports an active earthquake alert |
| `binary_sensor.sismo_detector` | safety | Sismo Detector reports an active alert |
| `binary_sensor.senapred_sae` | safety | An SAE message is active |
| `binary_sensor.tsunami` | safety | A tsunami bulletin is active |
| `binary_sensor.connection` | connectivity (diagnostic) | Relay WebSocket is connected |

Names depend on your language and entity naming settings. Source sensors only
exist for sources selected in the options flow.

### Attributes

Common attributes: `source`, `source_name`, `active`, `received_at`,
`active_since`, `attribution`.

Source-specific attributes:

- **CSN / Sismo Detector**: `magnitude`, `event_type`, `place`, `event_time`.
- **CSN**: `depth`.
- **Sismo Detector**: `status` (`preliminar`, `confirmado`, …).
- **SENAPRED SAE**: `message`.
- **Tsunami**: `state`, `zones`, `text`, `revision`, `bulletin_updated_at`.

Attributes are available whether the sensor is on or off, so the last clear
message remains inspectable.

## Sensors

| Entity | Meaning |
| --- | --- |
| `sensor.active_alerts` | Number of sources currently active |
| `sensor.last_alert` | Source name of the last message, with its attributes |
| `sensor.last_message` | Timestamp of the last relay message |

## Event

`sensor`-like event entity **Alert** fires once per relay envelope. Event
types are `csn`, `sismo_detector`, `senapred_sae`, and `tsunami`, and the event
data contains the same curated attributes as the binary sensor. Clears
(`active: false`) also fire, so automations can react to “alert ended”.
