"""Shared fixtures for the Alertas Chile test suite."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.alertas_chile.api import AlertasChileClient
from custom_components.alertas_chile.const import (
    CONF_SOURCES,
    DEFAULT_SOURCES,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Load custom components in every test."""
    yield


@pytest.fixture
def entry() -> MockConfigEntry:
    """Return a fully configured mock entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_SOURCES: list(DEFAULT_SOURCES)},
        unique_id=DOMAIN,
        version=1,
    )


@pytest.fixture
def no_websocket(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Keep the real relay out of tests."""

    async def _start(self: AlertasChileClient, hass: HomeAssistant) -> None:
        return None

    async def _stop(self: AlertasChileClient) -> None:
        return None

    monkeypatch.setattr(AlertasChileClient, "async_start", _start)
    monkeypatch.setattr(AlertasChileClient, "async_stop", _stop)
    return monkeypatch
