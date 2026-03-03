"""Evaluación de umbrales y despacho de alertas (terminal + Telegram)."""

from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import settings
from .scraper import FlightResult
from .telegram_notif import send_flight_alert

console = Console()


def _render_alert_panel(result: FlightResult, threshold: float) -> Panel:
    pct_below = (threshold - result.price_usd) / threshold * 100
    stops_str = "Directo" if result.stops == 0 else f"{result.stops} escala{'s' if result.stops > 1 else ''}"
    duration_str = f"{int(result.duration_hours)}h {int((result.duration_hours % 1) * 60)}m"

    body = Text()
    body.append(f"{result.origin} → {result.destination}", style="bold cyan")
    body.append(f"  |  USD {result.price_usd:,.0f}", style="bold green")
    body.append(f"\n¡{pct_below:.1f}% bajo tu umbral de ${threshold:,.0f}!\n", style="yellow")
    body.append(f"\n✈️  {result.airline}", style="white")
    body.append(f"  |  {stops_str}  |  {duration_str}\n", style="dim")
    body.append(f"📅  Salida: {result.departure_date}\n", style="white")
    body.append(f"📊  Fuente: {result.source}", style="dim")

    return Panel(
        body,
        title="[bold red]🛫 OFERTA DE VUELO[/bold red]",
        border_style="bright_red",
        expand=False,
    )


def evaluate_and_dispatch(
    results: list[FlightResult],
    threshold: float | None = None,
) -> list[FlightResult]:
    """
    Evalúa resultados contra el umbral y despacha alertas para los que lo superan.

    Args:
        results:   Lista de FlightResult a evaluar.
        threshold: Precio umbral en USD. Si es None, usa settings.flight_price_threshold_usd.

    Returns:
        Lista de resultados que estuvieron por debajo del umbral.
    """
    active_threshold = threshold if threshold is not None else settings.flight_price_threshold_usd
    triggered: list[FlightResult] = []

    for result in results:
        if result.price_usd < active_threshold:
            triggered.append(result)
            console.print(_render_alert_panel(result, active_threshold))
            send_flight_alert(result, active_threshold)

    if not triggered:
        console.print(
            f"[dim]Sin ofertas bajo el umbral de USD {active_threshold:,.0f} "
            f"({len(results)} vuelos revisados — {datetime.now().strftime('%H:%M:%S')})[/dim]"
        )

    return triggered
