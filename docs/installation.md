# Installation

## HACS

1. HACS → Integrations → ⋮ → Custom repositories.
2. Add `https://github.com/frabarz/hass-alertas` with category *Integration*.
3. Install **Alertas Chile** and restart Home Assistant.
4. Settings → Devices & Services → Add Integration → **Alertas Chile**.

The config flow performs one WebSocket handshake. If the relay is unreachable
the form shows `Could not reach the Alertas Chile relay` and no entry is
created.

## Manual

Copy `custom_components/alertas_chile/` into your Home Assistant
`config/custom_components/` directory and restart:

```bash
cp -r custom_components/alertas_chile /path/to/homeassistant/config/custom_components/
```

## NixOS

The flake exposes the integration as a package. Add it to the stock Home
Assistant module's `customComponents`:

```nix
{
  inputs.hass-alertas = {
    url = "github:frabarz/hass-alertas";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  # In your NixOS configuration (`inputs` is available via specialArgs):
  services.home-assistant = {
    enable = true;
    customComponents = [
      inputs.hass-alertas.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];
  };
}
```

Keep `inputs.nixpkgs.follows = "nixpkgs"` so the component is built against the
same Home Assistant version you run. Source selection stays in the Home
Assistant UI (there is no declarative YAML for this integration).

Or build the component derivation directly:

```bash
nix build .#alertas-chile-ha
# result/custom_components/alertas_chile/
```

## Requirements

- Home Assistant 2026.1 or newer.
- Outbound access to `wss://alertas.alertas-chile.fyi` (TLS, no credentials).
- No extra Python packages: only the standard library and the `aiohttp`
  session bundled with Home Assistant.
