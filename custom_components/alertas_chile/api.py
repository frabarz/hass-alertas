"""WebSocket transport for the Alertas Chile relay."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from contextlib import suppress
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    HEARTBEAT_S,
    RECONNECT_MAX_S,
    RECONNECT_MIN_S,
    REQUEST_TIMEOUT_S,
    SOURCES,
    WS_URL,
)
from .exceptions import AlertasChileConnectionError

_LOGGER = logging.getLogger(__name__)

MessageCallback = Callable[[str, dict[str, Any]], None]
ConnectionCallback = Callable[[bool], None]


class AlertasChileClient:
    """Maintain the relay WebSocket connection and dispatch envelopes.

    The relay is an unauthenticated push feed. It reconnects with exponential
    backoff, ignores malformed/unknown messages, and reports connection state
    changes so the coordinator can expose availability.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        url: str = WS_URL,
        on_message: MessageCallback | None = None,
        on_connection: ConnectionCallback | None = None,
    ) -> None:
        """Create a client bound to the Home Assistant aiohttp session."""
        self._session = session
        self._url = url
        self._on_message = on_message
        self._on_connection = on_connection
        self._task: asyncio.Task[None] | None = None
        self._connected = False

    def set_callbacks(
        self,
        on_message: MessageCallback,
        on_connection: ConnectionCallback,
    ) -> None:
        """Attach the coordinator callbacks."""
        self._on_message = on_message
        self._on_connection = on_connection

    async def async_start(self, hass: HomeAssistant) -> None:
        """Start the background connection loop (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._task = hass.async_create_background_task(
            self._async_run(), name=f"{DOMAIN}_websocket"
        )

    async def async_stop(self) -> None:
        """Cancel the connection loop and wait for it to finish."""
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def async_test_connection(self) -> None:
        """Open and immediately close a WebSocket handshake.

        Used by the config flow so a typo/unreachable relay is rejected at
        setup time instead of silently producing an entry that never updates.
        """
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_S):
                async with self._session.ws_connect(
                    self._url, heartbeat=HEARTBEAT_S
                ) as websocket:
                    await websocket.close()
        except (aiohttp.ClientError, TimeoutError, OSError) as err:
            raise AlertasChileConnectionError(str(err)) from err

    async def _async_run(self) -> None:
        """Connect forever, backing off after failures."""
        backoff = RECONNECT_MIN_S
        while True:
            try:
                async with self._session.ws_connect(
                    self._url, heartbeat=HEARTBEAT_S
                ) as websocket:
                    backoff = RECONNECT_MIN_S
                    self._notify_connection(True)
                    async for message in websocket:
                        if message.type is aiohttp.WSMsgType.TEXT:
                            self.handle_message(message.data)
                        elif message.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - keep the feed alive
                _LOGGER.warning("Alertas Chile relay error: %s", err)
            finally:
                # Report every failed attempt, not only transitions, so the
                # coordinator can escalate repeated unreachable relays.
                self._notify_connection(False)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, RECONNECT_MAX_S)

    def handle_message(self, raw: str | bytes) -> bool:
        """Parse one relay envelope and dispatch it.

        Returns ``True`` when a known source was dispatched. Invalid JSON,
        non-object payloads, and unknown sources are ignored.
        """
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return False
        if not isinstance(envelope, dict):
            return False
        source = envelope.get("source")
        data = envelope.get("data")
        if source not in SOURCES or not isinstance(data, dict):
            return False
        if self._on_message is not None:
            self._on_message(source, data)
        return True

    def _notify_connection(self, connected: bool) -> None:
        """Report successful connects once and every failed attempt."""
        if connected and self._connected:
            return
        self._connected = connected
        if self._on_connection is not None:
            self._on_connection(connected)
