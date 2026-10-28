"""Test helpers shared across modules."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alertas_chile.const import DOMAIN


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    """Add and set up a mock entry with the websocket client mocked."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()
    return entry


def entity_id_for(hass: HomeAssistant, domain: str, unique_id: str) -> str | None:
    """Look up an entity id by its unique id."""
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique_id)
