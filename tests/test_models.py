"""Unit tests for alert snapshot parsing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.alertas_chile.const import (
    CONF_SOURCES,
    SOURCE_CSN,
    SOURCE_NAMES,
    SOURCE_SENAPRED_SAE,
    SOURCE_SISMO_DETECTOR,
    SOURCE_TSUNAMI,
    SOURCES,
    enabled_sources,
)
from custom_components.alertas_chile.models import (
    AlertasChileData,
    AlertSnapshot,
)

NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


def test_bool_flag_parsing() -> None:
    """The relay must not treat the string ``"false"`` as active."""
    assert AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": True}, received_at=NOW
    ).active
    assert AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": "true"}, received_at=NOW
    ).active
    assert not AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": "false"}, received_at=NOW
    ).active
    assert not AlertSnapshot.from_envelope(SOURCE_CSN, {}, received_at=NOW).active


def test_csn_attributes() -> None:
    """CSN payload fields map to curated attributes."""
    snapshot = AlertSnapshot.from_envelope(
        SOURCE_CSN,
        {
            "active": True,
            "magnitud": "5.2",
            "tipo": "Sismo",
            "lugar": "20 km al oeste de Valparaíso",
            "profundidad": "35 km",
            "fecha": "2026-10-27 11:58:00",
        },
        received_at=NOW,
    )
    assert snapshot.magnitude == 5.2
    assert snapshot.event_type == "Sismo"
    assert snapshot.place == "20 km al oeste de Valparaíso"
    assert snapshot.depth == "35 km"
    assert snapshot.event_time == "2026-10-27 11:58:00"
    attrs = snapshot.attributes()
    assert attrs["source"] == SOURCE_CSN
    assert attrs["active"] is True
    assert attrs["magnitude"] == 5.2
    assert attrs["depth"] == "35 km"
    assert attrs["attribution"]


def test_sismo_detector_attributes() -> None:
    """Sismo Detector adds a status label and UTC time field."""
    snapshot = AlertSnapshot.from_envelope(
        SOURCE_SISMO_DETECTOR,
        {
            "active": True,
            "magnitud": 4.8,
            "tipo": "Sismo",
            "lugar": "Coquimbo",
            "hora": "12:00:00",
            "estado": "preliminar",
        },
        received_at=NOW,
    )
    attrs = snapshot.attributes()
    assert attrs["magnitude"] == 4.8
    assert attrs["event_time"] == "12:00:00"
    assert attrs["status"] == "preliminar"


def test_senapred_and_tsunami_attributes() -> None:
    """SAE exposes a message; tsunami exposes zones, revision, and timestamp."""
    sae = AlertSnapshot.from_envelope(
        SOURCE_SENAPRED_SAE,
        {"active": True, "mensaje": "Evacuar zona costera"},
        received_at=NOW,
    )
    assert sae.message == "Evacuar zona costera"
    assert sae.attributes()["message"] == "Evacuar zona costera"

    tsunami = AlertSnapshot.from_envelope(
        SOURCE_TSUNAMI,
        {
            "active": True,
            "estado": "alerta",
            "zonas": ["Arica", "Iquique"],
            "texto": "Boletín",
            "revision": "3",
            "ts": 1793000000,
        },
        received_at=NOW,
    )
    attrs = tsunami.attributes()
    assert attrs["state"] == "alerta"
    assert attrs["zones"] == ["Arica", "Iquique"]
    assert attrs["revision"] == 3
    assert attrs["bulletin_updated_at"] is not None


def test_active_since_is_preserved_and_reset() -> None:
    """An ongoing alert keeps its original start time; clears reset it."""
    first = AlertSnapshot.from_envelope(SOURCE_CSN, {"active": True}, received_at=NOW)
    later = NOW + timedelta(minutes=5)
    second = AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": True}, received_at=later, previous=first
    )
    assert second.active_since == NOW

    cleared = AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": False}, received_at=later, previous=second
    )
    assert cleared.active_since is None

    third = AlertSnapshot.from_envelope(
        SOURCE_CSN, {"active": True}, received_at=later, previous=cleared
    )
    assert third.active_since == later


def test_enabled_sources_defaults_and_filters() -> None:
    """Missing config means all sources; unknown/duplicate values are dropped."""
    assert enabled_sources({}, {}) == SOURCES
    assert enabled_sources({}, {CONF_SOURCES: [SOURCE_TSUNAMI, SOURCE_CSN]}) == (
        SOURCE_CSN,
        SOURCE_TSUNAMI,
    )
    assert enabled_sources({CONF_SOURCES: ["bogus"]}, {}) == ()
    assert enabled_sources({}, {CONF_SOURCES: "invalid"}) == SOURCES
    assert set(SOURCE_NAMES) == set(SOURCES)


def test_data_aggregates_active_sources_and_last_alert() -> None:
    """Only active snapshots count; the last message wins."""
    data = AlertasChileData()
    csn = AlertSnapshot.from_envelope(SOURCE_CSN, {"active": True}, received_at=NOW)
    sae = AlertSnapshot.from_envelope(
        SOURCE_SENAPRED_SAE, {"active": False}, received_at=NOW
    )
    data = data.with_message(SOURCE_CSN, csn).with_message(SOURCE_SENAPRED_SAE, sae)
    assert data.messages_received == 2
    assert data.active_sources == (SOURCE_CSN,)
    assert data.active_count == 1
    assert data.last_alert is sae
    assert data.alert_for(SOURCE_TSUNAMI) is None
