"""Diagnostics for Alertas Chile config entries.

The relay payload is public emergency information (no tokens, credentials,
or account identifiers), so the snapshot is returned as-is with curated
attributes. Options are included to debug source selection.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return connection telemetry and the latest alert snapshot."""
    data = entry.runtime_data.coordinator.data
    return {
        "domain": DOMAIN,
        "connected": data.connected,
        "connection_failures": data.connection_failures,
        "last_source": data.last_source,
        "last_message_at": (
            data.last_message_at.isoformat() if data.last_message_at else None
        ),
        "messages_received": data.messages_received,
        "active_sources": list(data.active_sources),
        "options": dict(entry.options),
        "alerts": {
            source: snapshot.attributes() for source, snapshot in data.alerts.items()
        },
    }
