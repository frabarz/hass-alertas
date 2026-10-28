"""Shared base entity for Alertas Chile."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import AlertasChileCoordinator


class AlertasChileEntity(CoordinatorEntity[AlertasChileCoordinator]):
    """Base entity bound to the relay coordinator and its single device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AlertasChileCoordinator) -> None:
        """Bind the entity and share the integration device."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            name=NAME,
            manufacturer=NAME,
            model="Emergency alert relay",
            configuration_url="https://alertas-chile.fyi",
        )
