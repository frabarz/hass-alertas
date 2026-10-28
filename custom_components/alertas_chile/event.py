"""Event entity firing once per relay message."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SOURCES
from .coordinator import AlertasChileCoordinator
from .entity import AlertasChileEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the single alert event entity."""
    coordinator: AlertasChileCoordinator = entry.runtime_data.coordinator
    async_add_entities([AlertasChileEventEntity(coordinator)])


class AlertasChileEventEntity(AlertasChileEntity, EventEntity):
    """Fire an event for every relay envelope, including clears."""

    _attr_translation_key = "alert"
    _attr_event_types = list(SOURCES)

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_alert"
        self._seen_messages = 0

    async def async_added_to_hass(self) -> None:
        """Skip events that happened before this entity existed."""
        await super().async_added_to_hass()
        data = self.coordinator.data
        self._seen_messages = data.messages_received if data is not None else 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire one event for each newly received relay message."""
        data = self.coordinator.data
        if data is not None and data.messages_received > self._seen_messages:
            self._seen_messages = data.messages_received
            snapshot = data.last_alert
            if snapshot is not None:
                self._trigger_event(snapshot.source, snapshot.attributes())
        super()._handle_coordinator_update()
