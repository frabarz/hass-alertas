"""Constants for the Alertas Chile integration.

The relay protocol was verified against the Alertas Chile Android app
(``assets/tv_overlay.html``): a plain WebSocket at ``WS_URL`` pushes JSON
envelopes of the form ``{"source": "...", "data": {...}}``. There is no
authentication, no polling, and every source publishes an ``active`` flag.

Sources (payload fields in parentheses):

* ``csn`` — Centro Sismológico Nacional (magnitud, tipo, lugar, profundidad,
  fecha, active).
* ``sismo_detector`` — Sismo Detector (magnitud, tipo, lugar, hora, estado,
  active).
* ``senapred_sae`` — SENAPRED SAE (mensaje, active).
* ``tsunami`` — SHOA/SENAPRED tsunami (estado, zonas, texto, revision, ts,
  active).
"""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "alertas_chile"
NAME: Final = "Alertas Chile"

WS_URL: Final = "wss://alertas.alertas-chile.fyi"
ATTRIBUTION: Final = "Datos: alertas-chile.fyi (no oficial)"

HEARTBEAT_S: Final = 30
REQUEST_TIMEOUT_S: Final = 10
RECONNECT_MIN_S: Final = 5
RECONNECT_MAX_S: Final = 60
FAILURES_BEFORE_REPAIR: Final = 3

SOURCE_CSN: Final = "csn"
SOURCE_SISMO_DETECTOR: Final = "sismo_detector"
SOURCE_SENAPRED_SAE: Final = "senapred_sae"
SOURCE_TSUNAMI: Final = "tsunami"

SOURCES: Final = (
    SOURCE_CSN,
    SOURCE_SISMO_DETECTOR,
    SOURCE_SENAPRED_SAE,
    SOURCE_TSUNAMI,
)

SOURCE_NAMES: Final = {
    SOURCE_CSN: "CSN",
    SOURCE_SISMO_DETECTOR: "Sismo Detector",
    SOURCE_SENAPRED_SAE: "SENAPRED SAE",
    SOURCE_TSUNAMI: "Tsunami",
}

CONF_SOURCES: Final = "sources"
DEFAULT_SOURCES: Final = list(SOURCES)

EVENT_ALERT: Final = f"{DOMAIN}_alert"


def enabled_sources(entry_data: dict, entry_options: dict) -> tuple[str, ...]:
    """Return the selected sources, defaulting to all of them.

    Unknown values are ignored and the original source order is preserved so
    entity creation stays deterministic across restarts.
    """
    raw = entry_options.get(CONF_SOURCES, entry_data.get(CONF_SOURCES))
    if raw is None:
        return SOURCES
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return SOURCES
    selected = set(raw)
    return tuple(source for source in SOURCES if source in selected)
