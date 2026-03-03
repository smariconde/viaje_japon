"""Scraping de precios de vuelos via fast-flights (Google Flights).

Itinerario asimétrico: EZE → NRT (salida) + BKK → EZE (vuelta desde Tailandia).
El precio reportado es la suma de ambos boletos one-way.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from urllib.parse import quote

from rich.console import Console

from .config import settings

console = Console()


@dataclass
class FlightResult:
    origin: str
    destination: str
    departure_date: str       # YYYY-MM-DD — vuelo de salida (EZE→NRT)
    price_usd: float          # precio combinado de ambos boletos
    airline: str = "Desconocida"
    duration_hours: float = 0.0
    stops: int = 1
    source: str = "fast-flights"
    return_origin: str = ""   # IATA del aeropuerto de vuelta (BKK)
    return_date: str = ""     # YYYY-MM-DD — vuelo de regreso (BKK→EZE)
    url: str = ""             # Google Flights — vuelo de salida
    return_url: str = ""      # Google Flights — vuelo de regreso


def _dates_for_month(year_month: str, flex_days: int = 7) -> list[str]:
    """Genera fechas flexibles alrededor del día 15 del mes dado (YYYY-MM)."""
    year, month = int(year_month[:4]), int(year_month[5:7])
    center = datetime.date(year, month, 15)
    dates = []
    for delta in range(-flex_days, flex_days + 1):
        d = center + datetime.timedelta(days=delta)
        if d.year == year and d.month == month:
            dates.append(d.strftime("%Y-%m-%d"))
    return dates


# ─── helpers ──────────────────────────────────────────────────────────────────

def _parse_stops(stops: object) -> int:
    try:
        return int(stops)
    except (ValueError, TypeError):
        return 1


def _parse_duration(duration: object) -> float:
    if isinstance(duration, (int, float)):
        return float(duration)
    if isinstance(duration, str):
        hours = int(re.search(r"(\d+)\s*h", duration).group(1)) if re.search(r"(\d+)\s*h", duration) else 0
        minutes = int(re.search(r"(\d+)\s*m", duration).group(1)) if re.search(r"(\d+)\s*m", duration) else 0
        return hours + minutes / 60
    return 0.0


def _gf_url(origin: str, destination: str, date: str) -> str:
    """URL de búsqueda en Google Flights para un vuelo one-way."""
    query = f"Flights to {destination} from {origin} on {date}"
    return f"https://www.google.com/travel/flights?hl=es&curr=USD&q={quote(query)}"


# ─── fast-flights ─────────────────────────────────────────────────────────────

def _fetch_oneway(origin: str, destination: str, departure_date: str) -> list[FlightResult]:
    """Consulta Google Flights via fast-flights para un tramo one-way."""
    try:
        from fast_flights import FlightData, Passengers
        from fast_flights.core import get_flights_from_filter
        from fast_flights.flights_impl import TFSData

        result = get_flights_from_filter(
            TFSData.from_interface(
                flight_data=[FlightData(date=departure_date, from_airport=origin, to_airport=destination)],
                trip="one-way",
                seat="economy",
                passengers=Passengers(adults=1),
                max_stops=2,
            ),
            currency="USD",
        )
        flights = []
        for f in result.flights:
            price = getattr(f, "price", None)
            if price is None:
                continue
            if isinstance(price, str):
                price = float(re.sub(r"[^\d.]", "", price.replace(",", "")))
            flights.append(FlightResult(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                price_usd=float(price),
                airline=getattr(f, "name", "Desconocida") or "Desconocida",
                duration_hours=_parse_duration(getattr(f, "duration", 0) or 0),
                stops=_parse_stops(getattr(f, "stops", 1)),
            ))
        return flights
    except Exception as exc:
        msg = str(exc).split("\n")[0][:120]
        console.print(f"[yellow]fast-flights ({origin}→{destination} {departure_date}): {msg}[/yellow]")
        return []


def _fetch_combined(
    origin: str,
    destination: str,
    departure_date: str,
    return_origin: str,
    return_date: str,
) -> list[FlightResult]:
    """Busca ambos tramos y devuelve un FlightResult con el precio combinado."""
    outbound = _fetch_oneway(origin, destination, departure_date)
    inbound = _fetch_oneway(return_origin, origin, return_date)

    if not outbound or not inbound:
        return []

    best_out = min(outbound, key=lambda r: r.price_usd)
    best_in = min(inbound, key=lambda r: r.price_usd)

    return [FlightResult(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        price_usd=best_out.price_usd + best_in.price_usd,
        airline=best_out.airline,
        duration_hours=best_out.duration_hours,
        stops=best_out.stops,
        source="fast-flights",
        return_origin=return_origin,
        return_date=return_date,
        url=_gf_url(origin, destination, departure_date),
        return_url=_gf_url(return_origin, origin, return_date),
    )]


# ─── Interfaz pública ─────────────────────────────────────────────────────────

def fetch_best_prices(
    year_month: str | None = None,
    flex_days: int = 7,
) -> list[FlightResult]:
    """
    Busca el costo total del viaje: EZE→NRT (salida) + BKK→EZE (vuelta desde Tailandia).

    Para cada fecha de salida genera combinaciones de estadías en Japón y Tailandia
    según settings.japan_stays × settings.thailand_stays.

    Args:
        year_month: Mes de salida en formato YYYY-MM. Si es None usa settings.months[0].
        flex_days:  Días de flexibilidad alrededor del día 15.

    Returns:
        Lista de FlightResult ordenada por precio total ascendente.
    """
    target_month = year_month or settings.months[0]
    dates = _dates_for_month(target_month, flex_days)
    return_origin = settings.return_origin_iata
    all_results: list[FlightResult] = []

    for destination in settings.destinations:
        for date in dates:
            date_obj = datetime.date.fromisoformat(date)
            for japan_days in settings.japan_stays:
                for thailand_days in settings.thailand_stays:
                    ret = (date_obj + datetime.timedelta(days=japan_days + thailand_days)).isoformat()
                    results = _fetch_combined(
                        settings.origin_iata, destination, date, return_origin, ret
                    )
                    all_results.extend(results)

    return sorted(all_results, key=lambda r: r.price_usd)
