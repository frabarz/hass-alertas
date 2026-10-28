"""Options flow: choose which relay sources create entities."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_SOURCES,
    SOURCE_NAMES,
    SOURCES,
    enabled_sources,
)


class AlertasChileOptionsFlow(OptionsFlow):
    """Select the sources whose entities are created for this entry."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Store the entry being configured."""
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Show the source multi-select."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = [
                source
                for source in SOURCES
                if source in user_input.get(CONF_SOURCES, [])
            ]
            if not selected:
                errors["base"] = "no_sources"
            else:
                return self.async_create_entry(title="", data={CONF_SOURCES: selected})
        current = list(enabled_sources(self._entry.data, self._entry.options))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCES, default=current): cv.multi_select(
                        {source: SOURCE_NAMES[source] for source in SOURCES}
                    )
                }
            ),
            errors=errors,
        )
