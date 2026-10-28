"""Unit tests for the WebSocket relay client."""

from __future__ import annotations

from typing import Any

import aiohttp
import pytest

from custom_components.alertas_chile.api import AlertasChileClient
from custom_components.alertas_chile.const import SOURCE_CSN
from custom_components.alertas_chile.exceptions import (
    AlertasChileConnectionError,
)


class _FakeWebSocket:
    """Async context manager returned by the fake session."""

    async def __aenter__(self) -> _FakeWebSocket:
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def close(self) -> None:
        return None


class _FakeSession:
    """Minimal aiohttp session stub."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def ws_connect(self, *args: Any, **kwargs: Any) -> Any:
        if self.error is not None:
            raise self.error
        return _FakeWebSocket()


def test_handle_message_dispatches_known_source() -> None:
    """A valid envelope reaches the callback and returns True."""
    received: list[tuple[str, dict[str, Any]]] = []
    client = AlertasChileClient(
        session=None,  # type: ignore[arg-type]
        on_message=lambda source, data: received.append((source, data)),
    )
    assert client.handle_message('{"source": "csn", "data": {"active": true}}')
    assert received == [(SOURCE_CSN, {"active": True})]


def test_handle_message_ignores_invalid_payloads() -> None:
    """Malformed JSON, unknown sources, and non-object data are dropped."""
    received: list[tuple[str, dict[str, Any]]] = []
    client = AlertasChileClient(
        session=None,  # type: ignore[arg-type]
        on_message=lambda source, data: received.append((source, data)),
    )
    assert not client.handle_message("not-json")
    assert not client.handle_message('{"source": "unknown", "data": {}}')
    assert not client.handle_message('{"source": "csn", "data": []}')
    assert not client.handle_message("[]")
    assert received == []


def test_connection_notifications_count_failed_attempts() -> None:
    """Successful connects notify once; every failed attempt is reported."""
    states: list[bool] = []
    client = AlertasChileClient(
        session=None,  # type: ignore[arg-type]
        on_connection=states.append,
    )
    client._notify_connection(True)
    client._notify_connection(True)
    client._notify_connection(False)
    client._notify_connection(False)
    assert states == [True, False, False]


async def test_test_connection_success() -> None:
    """A successful handshake returns without raising."""
    client = AlertasChileClient(_FakeSession())  # type: ignore[arg-type]
    await client.async_test_connection()


async def test_test_connection_failure() -> None:
    """Transport errors surface as AlertasChileConnectionError."""
    client = AlertasChileClient(
        _FakeSession(aiohttp.ClientError("boom"))  # type: ignore[arg-type]
    )
    with pytest.raises(AlertasChileConnectionError):
        await client.async_test_connection()
