"""Push coordinator for the Alertas Chile relay."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import AlertasChileClient
from .const import (
    DOMAIN,
    EVENT_ALERT,
    FAILURES_BEFORE_REPAIR,
    WS_URL,
)
from .models import AlertasChileData, AlertSnapshot

_LOGGER = logging.getLogger(__name__)


def unreachable_issue_id(entry: ConfigEntry) -> str:
    """Stable repair-issue id for the relay connection of one entry."""
    return f"backend_unreachable_{entry.entry_id}"


class AlertasChileCoordinator(DataUpdateCoordinator[AlertasChileData]):
    """Hold the latest relay snapshot and fan it out to entities.

    This is a push integration: there is no polling interval. The WebSocket
    client calls back into the coordinator, which stores an immutable snapshot
    and calls ``async_set_updated_data``.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AlertasChileClient,
    ) -> None:
        """Wire the client callbacks to this coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}-{entry.entry_id}",
            update_interval=None,
            always_update=False,
        )
        self.entry_id = entry.entry_id
        self._entry = entry
        self._client = client
        self._stopped = False
        self._client.set_callbacks(
            self.async_handle_message, self.async_handle_connection
        )

    async def _async_setup(self) -> None:
        """Start the relay feed before the first refresh completes."""
        await self._client.async_start(self.hass)

    async def _async_update_data(self) -> AlertasChileData:
        """Return the current push snapshot (there is nothing to poll)."""
        return self.data if self.data is not None else AlertasChileData()

    @callback
    def async_handle_message(self, source: str, data: dict[str, Any]) -> None:
        """Record a received relay envelope and notify listeners."""
        if self._stopped:
            return
        now: datetime = dt_util.utcnow()
        current = self.data or AlertasChileData()
        previous = current.alerts.get(source)
        snapshot = AlertSnapshot.from_envelope(
            source, data, received_at=now, previous=previous
        )
        updated = current.with_message(source, snapshot)
        self.async_set_updated_data(updated)
        self._delete_unreachable_issue()
        self.hass.bus.async_fire(
            EVENT_ALERT,
            {
                "source": source,
                "source_name": snapshot.source_name,
                "active": snapshot.active,
                "received_at": now.isoformat(),
                "data": dict(data),
            },
        )

    @callback
    def async_handle_connection(self, connected: bool) -> None:
        """Update connection telemetry and raise/dismiss repair issues."""
        if self._stopped:
            return
        current = self.data or AlertasChileData()
        failures = 0 if connected else current.connection_failures + 1
        self.async_set_updated_data(
            replace(
                current,
                connected=connected,
                connection_failures=failures,
            )
        )
        if connected:
            self._delete_unreachable_issue()
        elif failures >= FAILURES_BEFORE_REPAIR:
            self._create_unreachable_issue()

    async def async_stop(self) -> None:
        """Stop the feed and clear connection issues for this entry."""
        self._stopped = True
        self._delete_unreachable_issue()
        await self._client.async_stop()

    def _create_unreachable_issue(self) -> None:
        """Surface a persistent issue after repeated failed reconnects."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            unreachable_issue_id(self._entry),
            is_fixable=True,
            is_persistent=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="backend_unreachable",
            translation_placeholders={"url": WS_URL},
            data={"entry_id": self._entry.entry_id, "url": WS_URL},
        )

    def _delete_unreachable_issue(self) -> None:
        """Dismiss the unreachable issue once connected (or unloaded)."""
        ir.async_delete_issue(self.hass, DOMAIN, unreachable_issue_id(self._entry))
