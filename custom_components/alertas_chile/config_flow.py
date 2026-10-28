"""Config flow for Alertas Chile.

There are no credentials: the relay is a public WebSocket feed. The flow
performs one handshake so an unreachable relay is rejected at setup time.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlertasChileClient
from .const import CONF_SOURCES, DEFAULT_SOURCES, DOMAIN, NAME
from .exceptions import AlertasChileConnectionError


class AlertasChileConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the single-instance Alertas Chile setup."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Return the options flow (source selection)."""
        from .options_flow import AlertasChileOptionsFlow

        return AlertasChileOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verify the relay and create the entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            client = AlertasChileClient(async_get_clientsession(self.hass))
            try:
                await client.async_test_connection()
            except AlertasChileConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=NAME,
                    data={CONF_SOURCES: list(DEFAULT_SOURCES)},
                )
        return self.async_show_form(step_id="user", errors=errors)
