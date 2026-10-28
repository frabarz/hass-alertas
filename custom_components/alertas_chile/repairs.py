"""Repair flow for the Alertas Chile relay connection."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant


class BackendUnreachableRepairFlow(RepairsFlow):
    """Reload the entry to retry the WebSocket connection."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Enter the confirmation step."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Reload the entry after user confirmation."""
        if user_input is not None:
            assert self.data is not None
            await self.hass.config_entries.async_reload(str(self.data["entry_id"]))
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"url": str(self.data.get("url", ""))}
            if self.data
            else None,
        )


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    """Route unreachable-relay issues to their fix flow."""
    if issue_id.startswith("backend_unreachable_"):
        return BackendUnreachableRepairFlow()
    raise data_entry_flow.UnknownHandler
