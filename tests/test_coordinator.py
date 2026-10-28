"""Unit tests for the push coordinator."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.alertas_chile.const import (
    DOMAIN,
    EVENT_ALERT,
    FAILURES_BEFORE_REPAIR,
    SOURCE_CSN,
)
from custom_components.alertas_chile.coordinator import (
    AlertasChileCoordinator,
    unreachable_issue_id,
)


class _FakeClient:
    """Client stub recording lifecycle and callbacks."""

    def __init__(self) -> None:
        self.on_message = None
        self.on_connection = None
        self.started = False
        self.stopped = False

    def set_callbacks(self, on_message: Any, on_connection: Any) -> None:
        self.on_message = on_message
        self.on_connection = on_connection

    async def async_start(self, hass: HomeAssistant) -> None:
        self.started = True

    async def async_stop(self) -> None:
        self.stopped = True


def _coordinator(
    hass: HomeAssistant, entry: MockConfigEntry
) -> tuple[AlertasChileCoordinator, _FakeClient]:
    client = _FakeClient()
    return AlertasChileCoordinator(hass, entry, client), client


async def _start(coordinator: AlertasChileCoordinator) -> None:
    """Run the coordinator's one-time setup and initial refresh.

    ``async_config_entry_first_refresh`` is only valid while HA is setting up
    the entry; unit tests call the same two phases directly.
    """
    await coordinator._async_setup()
    await coordinator.async_refresh()


async def test_setup_starts_the_client(hass: HomeAssistant) -> None:
    """First refresh starts the relay feed and yields an empty snapshot."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=1)
    coordinator, client = _coordinator(hass, entry)
    await _start(coordinator)
    assert client.started
    assert coordinator.data is not None
    assert coordinator.data.connected is False
    assert coordinator.data.alerts == {}


async def test_message_updates_snapshot_and_fires_bus_event(
    hass: HomeAssistant,
) -> None:
    """Received envelopes update state and fire the integration event."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=1)
    coordinator, _ = _coordinator(hass, entry)
    await _start(coordinator)
    events = async_capture_events(hass, EVENT_ALERT)

    coordinator.async_handle_message(
        SOURCE_CSN,
        {"active": True, "magnitud": 5.2, "lugar": "Valparaíso"},
    )
    await hass.async_block_till_done()

    data = coordinator.data
    assert data is not None
    assert data.messages_received == 1
    assert data.last_source == SOURCE_CSN
    assert data.active_count == 1
    assert data.last_alert is not None
    assert data.last_alert.magnitude == 5.2
    assert events[0].data["source"] == SOURCE_CSN
    assert events[0].data["active"] is True


async def test_connection_failures_create_and_clear_issue(
    hass: HomeAssistant,
) -> None:
    """Repeated reconnects raise a repair issue; success dismisses it."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=1)
    coordinator, _ = _coordinator(hass, entry)
    await _start(coordinator)
    issue_id = unreachable_issue_id(entry)
    registry = ir.async_get(hass)

    for _ in range(FAILURES_BEFORE_REPAIR):
        coordinator.async_handle_connection(False)
    assert registry.async_get_issue(DOMAIN, issue_id) is not None
    assert coordinator.data is not None
    assert coordinator.data.connection_failures == FAILURES_BEFORE_REPAIR

    coordinator.async_handle_connection(True)
    assert registry.async_get_issue(DOMAIN, issue_id) is None
    assert coordinator.data is not None
    assert coordinator.data.connected is True
    assert coordinator.data.connection_failures == 0


async def test_stop_cancels_client_and_ignores_late_callbacks(
    hass: HomeAssistant,
) -> None:
    """Unloading stops the feed and late callbacks are ignored."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=1)
    coordinator, client = _coordinator(hass, entry)
    await _start(coordinator)

    await coordinator.async_stop()
    assert client.stopped
    coordinator.async_handle_message(SOURCE_CSN, {"active": True})
    assert coordinator.data is not None
    assert coordinator.data.messages_received == 0
