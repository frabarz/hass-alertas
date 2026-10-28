"""Integration-level tests for setup, unload, and entity state."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alertas_chile.const import (
    CONF_SOURCES,
    DOMAIN,
    SOURCE_CSN,
    SOURCE_SENAPRED_SAE,
    SOURCE_SISMO_DETECTOR,
    SOURCE_TSUNAMI,
)
from tests.helpers import entity_id_for, setup_entry

CSN_PAYLOAD = {
    "active": True,
    "magnitud": "5.2",
    "tipo": "Sismo",
    "lugar": "Valparaíso",
    "profundidad": "35 km",
    "fecha": "2026-10-27 11:58:00",
}


async def test_setup_creates_all_entities(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    no_websocket: object,
) -> None:
    """Every source, summary sensor, connectivity, and event entity exists."""
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    state = entry.runtime_data.coordinator.data
    assert state is not None and state.alerts == {}

    for source in (
        SOURCE_CSN,
        SOURCE_SISMO_DETECTOR,
        SOURCE_SENAPRED_SAE,
        SOURCE_TSUNAMI,
    ):
        assert (
            entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{source}_active")
            is not None
        )
    assert (
        entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_connection") is not None
    )
    for key in ("active_alerts", "last_alert", "last_message"):
        assert entity_id_for(hass, "sensor", f"{entry.entry_id}_{key}") is not None
    assert entity_id_for(hass, "event", f"{entry.entry_id}_alert") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_active_alert_updates_binary_sensor_and_summary(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    no_websocket: object,
) -> None:
    """A relay message drives the per-source sensor and summary sensors."""
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data.coordinator

    coordinator.async_handle_message(SOURCE_CSN, CSN_PAYLOAD)
    await hass.async_block_till_done()

    binary_id = entity_id_for(
        hass, "binary_sensor", f"{entry.entry_id}_{SOURCE_CSN}_active"
    )
    assert binary_id is not None
    state = hass.states.get(binary_id)
    assert state is not None
    assert state.state == "on"
    assert state.attributes["magnitude"] == 5.2
    assert state.attributes["place"] == "Valparaíso"
    assert state.attributes["source"] == SOURCE_CSN

    count_id = entity_id_for(hass, "sensor", f"{entry.entry_id}_active_alerts")
    assert count_id is not None
    assert hass.states.get(count_id).state == "1"  # type: ignore[union-attr]

    last_id = entity_id_for(hass, "sensor", f"{entry.entry_id}_last_alert")
    assert last_id is not None
    last_state = hass.states.get(last_id)
    assert last_state is not None
    assert last_state.state == "CSN"
    assert last_state.attributes["magnitude"] == 5.2

    message_id = entity_id_for(hass, "sensor", f"{entry.entry_id}_last_message")
    assert message_id is not None
    assert hass.states.get(message_id).state != "unknown"  # type: ignore[union-attr]


async def test_clearing_alert_turns_sensor_off(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    no_websocket: object,
) -> None:
    """A clear message flips the binary sensor off and resets the count."""
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data.coordinator
    coordinator.async_handle_message(SOURCE_CSN, {"active": True})
    coordinator.async_handle_message(SOURCE_CSN, {"active": False})
    await hass.async_block_till_done()

    binary_id = entity_id_for(
        hass, "binary_sensor", f"{entry.entry_id}_{SOURCE_CSN}_active"
    )
    assert binary_id is not None
    assert hass.states.get(binary_id).state == "off"  # type: ignore[union-attr]
    count_id = entity_id_for(hass, "sensor", f"{entry.entry_id}_active_alerts")
    assert count_id is not None
    assert hass.states.get(count_id).state == "0"  # type: ignore[union-attr]


async def test_event_entity_fires_per_message(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    no_websocket: object,
) -> None:
    """The event entity fires once per relay envelope."""
    await setup_entry(hass, entry)
    coordinator = entry.runtime_data.coordinator
    event_id = entity_id_for(hass, "event", f"{entry.entry_id}_alert")
    assert event_id is not None

    coordinator.async_handle_message(
        SOURCE_SENAPRED_SAE,
        {
            "active": True,
            "mensaje": "Evacuar",
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get(event_id)
    assert state is not None
    assert state.attributes["event_type"] == SOURCE_SENAPRED_SAE
    assert state.attributes["message"] == "Evacuar"


async def test_options_source_filter_limits_entities(
    hass: HomeAssistant,
    no_websocket: object,
) -> None:
    """Only selected sources create binary sensors; summaries always exist."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SOURCES: [SOURCE_CSN, SOURCE_TSUNAMI]},
        unique_id=DOMAIN,
        version=1,
    )
    await setup_entry(hass, entry)

    assert (
        entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{SOURCE_CSN}_active")
        is not None
    )
    assert (
        entity_id_for(
            hass, "binary_sensor", f"{entry.entry_id}_{SOURCE_TSUNAMI}_active"
        )
        is not None
    )
    assert (
        entity_id_for(
            hass,
            "binary_sensor",
            f"{entry.entry_id}_{SOURCE_SISMO_DETECTOR}_active",
        )
        is None
    )
    assert entity_id_for(hass, "sensor", f"{entry.entry_id}_active_alerts") is not None
