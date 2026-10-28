"""Error taxonomy for the Alertas Chile relay client."""

from __future__ import annotations


class AlertasChileError(Exception):
    """Base error for the Alertas Chile integration."""


class AlertasChileConnectionError(AlertasChileError):
    """The relay could not be reached or the handshake failed."""
