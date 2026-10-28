"""Repair flow routing and form tests."""

from __future__ import annotations

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.alertas_chile.repairs import (
    BackendUnreachableRepairFlow,
    async_create_fix_flow,
)


async def test_create_fix_flow_routes_unreachable_issue(
    hass: HomeAssistant,
) -> None:
    """The unreachable issue opens the retry flow; unknown ids are rejected."""
    flow = await async_create_fix_flow(
        hass, "backend_unreachable_entry", {"entry_id": "entry"}
    )
    assert isinstance(flow, BackendUnreachableRepairFlow)

    with pytest.raises(data_entry_flow.UnknownHandler):
        await async_create_fix_flow(hass, "other_issue", None)


async def test_repair_flow_confirm_form_shows_url(hass: HomeAssistant) -> None:
    """The confirmation form is translated and exposes the relay URL."""
    flow = BackendUnreachableRepairFlow()
    flow.hass = hass
    flow.data = {"entry_id": "entry", "url": "wss://example.invalid"}

    result = await flow.async_step_init()
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {"url": "wss://example.invalid"}
