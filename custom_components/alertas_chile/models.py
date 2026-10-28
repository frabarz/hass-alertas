"""Typed alert snapshots and relay state for Alertas Chile."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    SOURCE_CSN,
    SOURCE_NAMES,
    SOURCE_SENAPRED_SAE,
    SOURCE_SISMO_DETECTOR,
    SOURCE_TSUNAMI,
    SOURCES,
)

TRUTHY = frozenset({"1", "true", "yes", "on", "active"})


def _as_bool(value: Any) -> bool:
    """Parse the relay's boolean flags without treating ``"false"`` as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY
    return False


def _as_text(value: Any) -> str | None:
    """Return a trimmed non-empty string, or ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_float(value: Any) -> float | None:
    """Return a finite float, or ``None`` when the field is missing/invalid."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _as_int(value: Any) -> int | None:
    """Return an int, or ``None`` when the field is missing/invalid."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_ts(value: Any) -> datetime | None:
    """Convert an epoch-seconds field to an aware UTC datetime."""
    seconds = _as_float(value)
    if seconds is None:
        return None
    try:
        return dt_util.utc_from_timestamp(seconds)
    except (OverflowError, OSError, ValueError):
        return None


def _as_str_list(value: Any) -> tuple[str, ...]:
    """Normalize a list of display strings."""
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(text for item in value if (text := _as_text(item)) is not None)


@dataclass(frozen=True)
class AlertSnapshot:
    """Latest relay state for one source."""

    source: str
    active: bool
    data: Mapping[str, Any]
    received_at: datetime
    active_since: datetime | None = None

    @classmethod
    def from_envelope(
        cls,
        source: str,
        data: Mapping[str, Any],
        *,
        received_at: datetime,
        previous: AlertSnapshot | None = None,
    ) -> AlertSnapshot:
        """Build a snapshot, preserving when an ongoing alert started."""
        active = _as_bool(data.get("active"))
        active_since: datetime | None = None
        if active:
            active_since = (
                previous.active_since
                if previous is not None and previous.active_since is not None
                else received_at
            )
        return cls(
            source=source,
            active=active,
            data=dict(data),
            received_at=received_at,
            active_since=active_since,
        )

    @property
    def source_name(self) -> str:
        """Human-readable source name."""
        return SOURCE_NAMES.get(self.source, self.source)

    @property
    def magnitude(self) -> float | None:
        """Earthquake magnitude (CSN and Sismo Detector)."""
        if self.source not in (SOURCE_CSN, SOURCE_SISMO_DETECTOR):
            return None
        return _as_float(self.data.get("magnitud"))

    @property
    def event_type(self) -> str | None:
        """Earthquake type reported by CSN/Sismo Detector."""
        if self.source not in (SOURCE_CSN, SOURCE_SISMO_DETECTOR):
            return None
        return _as_text(self.data.get("tipo"))

    @property
    def place(self) -> str | None:
        """Epicenter or referenced location."""
        if self.source not in (SOURCE_CSN, SOURCE_SISMO_DETECTOR):
            return None
        return _as_text(self.data.get("lugar"))

    @property
    def depth(self) -> str | None:
        """CSN depth as published by the backend (usually ``"35 km"``)."""
        if self.source != SOURCE_CSN:
            return None
        return _as_text(self.data.get("profundidad"))

    @property
    def event_time(self) -> str | None:
        """Event time exactly as published by the source."""
        if self.source == SOURCE_CSN:
            return _as_text(self.data.get("fecha"))
        if self.source == SOURCE_SISMO_DETECTOR:
            return _as_text(self.data.get("hora"))
        return None

    @property
    def status(self) -> str | None:
        """Status label (``"preliminar"``, ``"confirmado"``, ...)."""
        if self.source != SOURCE_SISMO_DETECTOR:
            return None
        return _as_text(self.data.get("estado"))

    @property
    def message(self) -> str | None:
        """SENAPRED SAE message text."""
        if self.source != SOURCE_SENAPRED_SAE:
            return None
        return _as_text(self.data.get("mensaje"))

    @property
    def state(self) -> str | None:
        """Tsunami advisory state (``"alerta"``, ``"precaucion"``, ...)."""
        if self.source != SOURCE_TSUNAMI:
            return None
        return _as_text(self.data.get("estado"))

    @property
    def zones(self) -> tuple[str, ...]:
        """Tsunami zones named in the bulletin."""
        if self.source != SOURCE_TSUNAMI:
            return ()
        return _as_str_list(self.data.get("zonas"))

    @property
    def text(self) -> str | None:
        """Tsunami bulletin body."""
        if self.source != SOURCE_TSUNAMI:
            return None
        return _as_text(self.data.get("texto"))

    @property
    def revision(self) -> int | None:
        """Tsunami bulletin revision number."""
        if self.source != SOURCE_TSUNAMI:
            return None
        return _as_int(self.data.get("revision"))

    @property
    def bulletin_updated_at(self) -> datetime | None:
        """Timestamp embedded in the tsunami payload (epoch seconds)."""
        if self.source != SOURCE_TSUNAMI:
            return None
        return _as_ts(self.data.get("ts"))

    def attributes(self) -> dict[str, Any]:
        """Curated, serializable attributes for entities and diagnostics."""
        attributes: dict[str, Any] = {
            "source": self.source,
            "source_name": self.source_name,
            "active": self.active,
            "received_at": self.received_at.isoformat(),
            "active_since": (
                self.active_since.isoformat() if self.active_since else None
            ),
            "attribution": ATTRIBUTION,
        }
        if self.source in (SOURCE_CSN, SOURCE_SISMO_DETECTOR):
            attributes.update(
                {
                    "magnitude": self.magnitude,
                    "event_type": self.event_type,
                    "place": self.place,
                    "event_time": self.event_time,
                }
            )
        if self.source == SOURCE_CSN:
            attributes["depth"] = self.depth
        if self.source == SOURCE_SISMO_DETECTOR:
            attributes["status"] = self.status
        if self.source == SOURCE_SENAPRED_SAE:
            attributes["message"] = self.message
        if self.source == SOURCE_TSUNAMI:
            attributes.update(
                {
                    "state": self.state,
                    "zones": list(self.zones),
                    "text": self.text,
                    "revision": self.revision,
                    "bulletin_updated_at": (
                        self.bulletin_updated_at.isoformat()
                        if self.bulletin_updated_at
                        else None
                    ),
                }
            )
        return attributes


@dataclass(frozen=True)
class AlertasChileData:
    """One relay snapshot: per-source alerts plus connection telemetry."""

    alerts: Mapping[str, AlertSnapshot] = field(default_factory=dict)
    connected: bool = False
    last_message_at: datetime | None = None
    last_source: str | None = None
    messages_received: int = 0
    connection_failures: int = 0

    def alert_for(self, source: str) -> AlertSnapshot | None:
        """Return the latest snapshot for one source."""
        return self.alerts.get(source)

    @property
    def active_sources(self) -> tuple[str, ...]:
        """Sources currently reporting an active alert, in stable order."""
        return tuple(
            source
            for source in SOURCES
            if (snapshot := self.alerts.get(source)) is not None and snapshot.active
        )

    @property
    def active_count(self) -> int:
        """Number of sources with an active alert."""
        return len(self.active_sources)

    @property
    def last_alert(self) -> AlertSnapshot | None:
        """Snapshot that produced the most recent relay message."""
        if self.last_source is None:
            return None
        return self.alerts.get(self.last_source)

    def with_message(self, source: str, snapshot: AlertSnapshot) -> AlertasChileData:
        """Return a copy carrying a newly received alert."""
        return replace(
            self,
            alerts={**self.alerts, source: snapshot},
            last_message_at=snapshot.received_at,
            last_source=source,
            messages_received=self.messages_received + 1,
        )
