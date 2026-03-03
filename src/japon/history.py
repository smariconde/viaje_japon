"""Persistencia de historial de precios en data/price_history.json."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import DATA_DIR, PRICE_HISTORY_FILE
from .scraper import FlightResult


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    """Carga el historial desde JSON. Devuelve lista vacía si no existe."""
    if not PRICE_HISTORY_FILE.exists():
        return []
    try:
        return json.loads(PRICE_HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def append_results(results: list[FlightResult]) -> None:
    """Agrega nuevos resultados al historial, preservando los anteriores."""
    _ensure_data_dir()
    history = load_history()
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for r in results:
        history.append(
            {
                "checked_at": timestamp,
                "origin": r.origin,
                "destination": r.destination,
                "departure_date": r.departure_date,
                "return_origin": r.return_origin,
                "return_date": r.return_date,
                "price_usd": r.price_usd,
                "airline": r.airline,
                "duration_hours": r.duration_hours,
                "stops": r.stops,
                "source": r.source,
                "url": r.url,
                "return_url": r.return_url,
            }
        )
    PRICE_HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_cheapest_ever() -> dict | None:
    """Devuelve el registro con el precio más bajo del historial."""
    history = load_history()
    if not history:
        return None
    return min(history, key=lambda r: r["price_usd"])


def get_recent(limit: int = 20) -> list[dict]:
    """Devuelve los últimos N registros del historial."""
    history = load_history()
    return history[-limit:]
