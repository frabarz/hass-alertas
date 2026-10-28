"""Sensors summarizing the Alertas Chile relay."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION
from .coordinator import AlertasChileCoordinator
from .entity import AlertasChileEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the relay summary sensors."""
    coordinator: AlertasChileCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            AlertasChileActiveCountSensor(coordinator),
            AlertasChileLastAlertSensor(coordinator),
            AlertasChileLastMessageSensor(coordinator),
        ]
    )


class _AlertasChileSensor(AlertasChileEntity, SensorEntity):
    """Shared constructor for the summary sensors."""

    def __init__(self, coordinator: AlertasChileCoordinator, key: str) -> None:
        """Bind the sensor and derive a stable unique id."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_{key}"
        self._attr_translation_key = key


class AlertasChileActiveCountSensor(_AlertasChileSensor):
    """How many sources are currently reporting an active alert."""

    _attr_icon = "mdi:alert-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the active-count sensor."""
        super().__init__(coordinator, "active_alerts")

    @property
    def native_value(self) -> int | None:
        """Return the number of active sources, or unknown before any push."""
        data = self.coordinator.data
        if data is None or data.messages_received == 0:
            return None
        return data.active_count


class AlertasChileLastAlertSensor(_AlertasChileSensor):
    """Source name of the most recently received alert message."""

    _attr_icon = "mdi:alert-outline"

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the last-alert sensor."""
        super().__init__(coordinator, "last_alert")

    @property
    def native_value(self) -> str | None:
        """Return the source name of the last relay message."""
        data = self.coordinator.data
        snapshot = data.last_alert if data is not None else None
        if snapshot is None:
            return None
        return snapshot.source_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the last alert details."""
        data = self.coordinator.data
        snapshot = data.last_alert if data is not None else None
        if snapshot is None:
            return {"attribution": ATTRIBUTION}
        return snapshot.attributes()


class AlertasChileLastMessageSensor(_AlertasChileSensor):
    """Timestamp of the last relay message, regardless of active state."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the last-message timestamp sensor."""
        super().__init__(coordinator, "last_message")

    @property
    def native_value(self) -> datetime | None:
        """Return the last message timestamp."""
        data = self.coordinator.data
        return data.last_message_at if data is not None else None
