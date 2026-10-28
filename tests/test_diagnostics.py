"""Diagnostics tests: connection telemetry and alert snapshot."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alertas_chile.const import SOURCE_CSN
from custom_components.alertas_chile.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.helpers import setup_entry


async def test_diagnostics_reports_snapshot(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    no_websocket: object,
) -> None:
    """Connection state, options, and curated alert data are exported."""
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data.coordinator
    coordinator.async_handle_connection(True)
    coordinator.async_handle_message(
        SOURCE_CSN,
        {
            "active": True,
            "magnitud": 5.2,
            "lugar": "Valparaíso",
            "profundidad": "35 km",
        },
    )
    await hass.async_block_till_done()

    payload = await async_get_config_entry_diagnostics(hass, entry)
    assert payload["connected"] is True
    assert payload["messages_received"] == 1
    assert payload["last_source"] == SOURCE_CSN
    assert payload["active_sources"] == [SOURCE_CSN]
    assert payload["alerts"][SOURCE_CSN]["magnitude"] == 5.2
    assert payload["alerts"][SOURCE_CSN]["place"] == "Valparaíso"
    assert "options" in payload
