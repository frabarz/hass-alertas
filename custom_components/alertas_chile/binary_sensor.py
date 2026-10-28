"""Binary sensors for the Alertas Chile relay."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, enabled_sources
from .coordinator import AlertasChileCoordinator
from .entity import AlertasChileEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one active-alert sensor per selected source."""
    coordinator: AlertasChileCoordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        AlertActiveBinarySensor(coordinator, source)
        for source in enabled_sources(entry.data, entry.options)
    ]
    entities.append(AlertConnectionBinarySensor(coordinator))
    async_add_entities(entities)


class AlertActiveBinarySensor(AlertasChileEntity, BinarySensorEntity):
    """On while the source reports an active emergency alert."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: AlertasChileCoordinator, source: str) -> None:
        """Bind the sensor to one relay source."""
        super().__init__(coordinator)
        self._source = source
        self._attr_unique_id = f"{coordinator.entry_id}_{source}_active"
        self._attr_translation_key = f"{source}_alert"

    @property
    def is_on(self) -> bool | None:
        """Return whether the source is active, or unknown before its first push."""
        data = self.coordinator.data
        snapshot = data.alert_for(self._source) if data is not None else None
        if snapshot is None:
            return None
        return snapshot.active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the source-specific alert details."""
        data = self.coordinator.data
        snapshot = data.alert_for(self._source) if data is not None else None
        if snapshot is None:
            return {"attribution": ATTRIBUTION}
        return snapshot.attributes()


class AlertConnectionBinarySensor(AlertasChileEntity, BinarySensorEntity):
    """Diagnostic connectivity sensor for the relay WebSocket."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connection"

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the connectivity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_connection"

    @property
    def is_on(self) -> bool:
        """Return whether the relay connection is up."""
        data = self.coordinator.data
        return bool(data is not None and data.connected)
