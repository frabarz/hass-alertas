# Arguments are resolved from the home-assistant.python3Packages scope.
# Call via pkgs.home-assistant.python3Packages.callPackage, NOT
# pkgs.callPackage, so buildHomeAssistantComponent and any future Python
# deps come from HA's pinned interpreter set.
{
  lib,
  buildHomeAssistantComponent,
  src,
}:

buildHomeAssistantComponent rec {
  owner = "frabarz";
  domain = "alertas_chile";
  version = "0.1.0";

  inherit src;

  # Zero runtime dependencies: the relay is a plain WebSocket consumed with
  # the aiohttp client session bundled with Home Assistant.
  meta = {
    description = "Alertas Chile emergency-alert relay for Home Assistant";
    homepage = "https://github.com/frabarz/hass-alertas";
    license = lib.licenses.mit;
    maintainers = [ ];
  };
}
