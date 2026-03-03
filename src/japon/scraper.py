"""Scraping de precios de vuelos — fast-flights (Google Flights) + fallback Amadeus."""

from __future__ import annotations

import datetime
import time
from dataclasses import dataclass, field

from rich.console import Console

from .config import settings

# Delay entre llamadas a Amadeus para no superar el rate limit del free tier (~10 req/s)
_AMADEUS_DELAY_SECONDS = 0.5

console = Console()


@dataclass
class FlightResult:
    origin: str
    destination: str
    departure_date: str          # YYYY-MM-DD
    price_usd: float
    airline: str = "Desconocida"
    duration_hours: float = 0.0
    stops: int = 1
    source: str = "fast-flights"  # "fast-flights" | "amadeus"
    url: str = ""


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


# ─── fast-flights ─────────────────────────────────────────────────────────────

def _fetch_fast_flights(
    origin: str,
    destination: str,
    departure_date: str,
) -> list[FlightResult]:
    """Consulta Google Flights via fast-flights para una ruta y fecha."""
    try:
        from fast_flights import FlightData, Passengers, create_filter, get_flights

        filter_ = create_filter(
            flight_data=[
                FlightData(date=departure_date, from_airport=origin, to_airport=destination)
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            max_stops=2,
        )
        result = get_flights(filter_)
        flights = []
        for f in result.flights:
            price = getattr(f, "price", None)
            if price is None:
                continue
            # fast-flights puede devolver precio como string "$1,234" o float
            if isinstance(price, str):
                price = float(price.replace("$", "").replace(",", "").strip())
            flights.append(
                FlightResult(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    price_usd=float(price),
                    airline=getattr(f, "name", "Desconocida") or "Desconocida",
                    duration_hours=getattr(f, "duration", 0) or 0,
                    stops=getattr(f, "stops", 1) or 1,
                    source="fast-flights",
                )
            )
        return flights
    except Exception as exc:
        console.print(f"[yellow]fast-flights error ({origin}→{destination} {departure_date}): {exc}[/yellow]")
        return []


# ─── Amadeus fallback ─────────────────────────────────────────────────────────

def _fetch_amadeus(
    origin: str,
    destination: str,
    departure_date: str,
) -> list[FlightResult]:
    """Consulta Amadeus Flight Offers Search API (fallback)."""
    if not settings.amadeus_enabled:
        return []
    try:
        from amadeus import Client, ResponseError

        amadeus = Client(
            client_id=settings.amadeus_api_key,
            client_secret=settings.amadeus_api_secret,
        )
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1,
            currencyCode="USD",
            max=5,
        )
        flights = []
        for offer in response.data:
            price = float(offer["price"]["total"])
            itinerary = offer["itineraries"][0]
            segments = itinerary["segments"]
            carrier = segments[0]["carrierCode"]
            stops = len(segments) - 1
            # Duración en formato PT5H30M → horas float
            duration_str = itinerary.get("duration", "PT0H")
            hours = _parse_iso_duration(duration_str)
            flights.append(
                FlightResult(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    price_usd=price,
                    airline=carrier,
                    duration_hours=hours,
                    stops=stops,
                    source="amadeus",
                )
            )
        return flights
    except Exception as exc:
        console.print(f"[yellow]Amadeus error ({origin}→{destination} {departure_date}): {exc}[/yellow]")
        return []


def _parse_iso_duration(duration: str) -> float:
    """Convierte PT5H30M → 5.5 horas."""
    import re
    hours = int(re.search(r"(\d+)H", duration).group(1)) if "H" in duration else 0
    minutes = int(re.search(r"(\d+)M", duration).group(1)) if "M" in duration else 0
    return hours + minutes / 60


# ─── Interfaz pública ─────────────────────────────────────────────────────────

def fetch_best_prices(
    year_month: str | None = None,
    flex_days: int = 7,
) -> list[FlightResult]:
    """
    Busca los mejores precios para BUE → TYO (o destinos configurados).

    Args:
        year_month: Mes objetivo en formato YYYY-MM. Si es None usa settings.months[0].
        flex_days:  Días de flexibilidad alrededor del día 15.

    Returns:
        Lista de FlightResult ordenada por precio ascendente.
    """
    target_month = year_month or settings.months[0]
    dates = _dates_for_month(target_month, flex_days)
    all_results: list[FlightResult] = []

    amadeus_used = False
    for destination in settings.destinations:
        for date in dates:
            results = _fetch_fast_flights(settings.origin_iata, destination, date)
            if not results:
                if amadeus_used:
                    time.sleep(_AMADEUS_DELAY_SECONDS)
                results = _fetch_amadeus(settings.origin_iata, destination, date)
                amadeus_used = True
            all_results.extend(results)

    return sorted(all_results, key=lambda r: r.price_usd)
