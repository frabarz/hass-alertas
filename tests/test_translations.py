"""Translation parity and completeness for Alertas Chile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRANS = Path("custom_components/alertas_chile/translations")


def _load(lang: str) -> dict[str, Any]:
    return json.loads((TRANS / f"{lang}.json").read_text())


def _leaves(node: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            out.update(_leaves(value, f"{prefix}.{key}" if prefix else key))
    else:
        out[prefix] = node
    return out


def test_translation_key_parity_and_content() -> None:
    """Both locales expose identical keys with non-empty literal text."""
    en = _leaves(_load("en"))
    es = _leaves(_load("es"))
    assert set(en) == set(es)
    texts = (*en.values(), *es.values())
    assert all(isinstance(text, str) and text.strip() for text in texts)


def test_required_flow_and_entity_keys_present() -> None:
    """Every step, error, entity, and issue the integration uses is translated."""
    en = _load("en")
    assert en["title"] == "Alertas Chile"
    assert set(en["config"]["step"]) == {"user"}
    assert set(en["config"]["error"]) >= {"cannot_connect"}
    assert set(en["config"]["abort"]) >= {"already_configured"}
    assert set(en["options"]["step"]) == {"init"}
    assert set(en["options"]["error"]) >= {"no_sources"}
    assert set(en["entity"]["sensor"]) == {
        "active_alerts",
        "last_alert",
        "last_message",
    }
    assert set(en["entity"]["binary_sensor"]) == {
        "connection",
        "csn_alert",
        "sismo_detector_alert",
        "senapred_sae_alert",
        "tsunami_alert",
    }
    assert set(en["entity"]["event"]) == {"alert"}
    assert set(en["issues"]) >= {"backend_unreachable"}


def test_no_core_placeholders() -> None:
    """Custom integrations must ship literal text, not build-time keys."""
    for lang in ("en", "es"):
        text = (TRANS / f"{lang}.json").read_text()
        assert "[%key" not in text
