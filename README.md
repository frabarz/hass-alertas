# Alertas Chile — Home Assistant integration

Emergency alerts from [Alertas Chile](https://alertas-chile.fyi/) (CSN
earthquakes, Sismo Detector, SENAPRED SAE, and tsunami bulletins) pushed live
into Home Assistant through the public relay WebSocket.

> **Unofficial integration, no affiliation with Alertas Chile, CSN, SENAPRED,
> SHOA, or Sismo Detector.** The relay is a public push feed and may change
> without notice.

> [!CAUTION]
> This integration is an automation convenience, not a replacement for official
> warnings, SAE messages, or evacuation instructions.  
> Never rely on Home Assistant alone for life-safety decisions.

## What it does

Add the integration once (no account or credentials), then every relay
message updates a shared device:

- **Source binary sensors** — one per source (`CSN`, `Sismo Detector`,
  `SENAPRED SAE`, `Tsunami`); on while that source reports an active alert.
  Attributes carry the source-specific detail (magnitude, place, depth, SAE
  message, tsunami zones/revision, …).
- **Connection** — diagnostic binary sensor for the relay WebSocket.
- **Active alerts** — how many sources are currently active.
- **Last alert** — source name plus the last alert's attributes.
- **Last message** — timestamp of the most recent relay message.
- **Alert event** — an event entity that fires on every relay envelope,
  including clears (`active: false`), for automations.

Sources can be selected in the integration options. Everything is local to
Home Assistant; the integration makes no HTTP API calls, only the WebSocket
connection.

Works in English and Spanish. Requires Home Assistant 2026.1 or newer.

## Install

Via HACS (recommended):

1. HACS → Integrations → ⋮ → Custom repositories → add this repo URL
   (category *Integration*).
2. Install “Alertas Chile”, restart Home Assistant.
3. Settings → Devices & Services → Add Integration → Alertas Chile.

Details and alternatives (manual install, NixOS flake):
[docs/installation.md](docs/installation.md).

## Documentation

- [Configuration](docs/configuration.md) — sources, options, relays.
- [Entities](docs/entities.md) — binary sensors, summaries, event, attributes.
- [Dashboards](docs/dashboards.md) — cards and notification automations.
- [Troubleshooting](docs/troubleshooting.md) — connection issues and repair.

## Development

```bash
nix develop            # Linux: HA dev shell + pytest + ruff
pytest tests/
ruff check . && ruff format --check .
nix build .#alertas-chile-ha
nix flake check
```

On macOS the default shell is the APK research shell (HA's native dependency
chain does not build reliably on darwin); use a Linux nix dev shell or CI for
`pytest`.

Implementation notes live in [AGENTS.md](AGENTS.md). The relay envelope
schema and per-source fields were verified against the Android app's
`assets/tv_overlay.html`.
