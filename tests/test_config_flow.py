"""Unit tests for the Alertas Chile config and options flows."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alertas_chile.api import AlertasChileClient
from custom_components.alertas_chile.const import (
    CONF_SOURCES,
    DOMAIN,
    SOURCE_CSN,
    SOURCE_TSUNAMI,
)
from custom_components.alertas_chile.exceptions import (
    AlertasChileConnectionError,
)


async def test_user_flow_creates_entry(hass: HomeAssistant, monkeypatch) -> None:
    """A successful handshake creates the single entry."""

    async def _ok(self: AlertasChileClient) -> None:
        return None

    monkeypatch.setattr(AlertasChileClient, "async_test_connection", _ok)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Alertas Chile"
    assert result["data"][CONF_SOURCES]


async def test_user_flow_rejects_duplicate(hass: HomeAssistant, monkeypatch) -> None:
    """The integration is single-instance."""

    async def _ok(self: AlertasChileClient) -> None:
        return None

    monkeypatch.setattr(AlertasChileClient, "async_test_connection", _ok)
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_reports_unreachable_relay(
    hass: HomeAssistant, monkeypatch
) -> None:
    """A failed handshake keeps the form open with cannot_connect."""

    async def _fail(self: AlertasChileClient) -> None:
        raise AlertasChileConnectionError("unreachable")

    monkeypatch.setattr(AlertasChileClient, "async_test_connection", _fail)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow_updates_sources(hass: HomeAssistant) -> None:
    """Options flow persists the selected sources."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SOURCES: [SOURCE_CSN]},
        unique_id=DOMAIN,
        version=1,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SOURCES: [SOURCE_TSUNAMI]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SOURCES] == [SOURCE_TSUNAMI]


async def test_options_flow_requires_a_source(hass: HomeAssistant) -> None:
    """An empty selection is rejected instead of creating an entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SOURCES: [SOURCE_CSN]},
        unique_id=DOMAIN,
        version=1,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SOURCES: []}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_sources"}
    assert entry.options == {}
