"""The Alertas Chile integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlertasChileClient
from .const import DOMAIN
from .coordinator import AlertasChileCoordinator, unreachable_issue_id

PLATFORMS: list[str] = ["binary_sensor", "sensor", "event"]


@dataclass
class AlertasChileRuntimeData:
    """Shared objects for one Alertas Chile entry."""

    client: AlertasChileClient
    coordinator: AlertasChileCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the relay feed and its platforms."""
    client = AlertasChileClient(async_get_clientsession(hass))
    coordinator = AlertasChileCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = AlertasChileRuntimeData(client=client, coordinator=coordinator)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when source selection changes so entities appear/disappear."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload platforms and stop the WebSocket feed."""
    data: AlertasChileRuntimeData | None = getattr(entry, "runtime_data", None)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and data is not None:
        await data.coordinator.async_stop()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear the connection repair issue when the entry is deleted."""
    ir.async_delete_issue(hass, DOMAIN, unreachable_issue_id(entry))


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries; v1 has nothing to migrate yet."""
    return True
