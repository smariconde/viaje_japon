"""Notificaciones via Telegram — python-telegram-bot."""

from __future__ import annotations

import asyncio

from rich.console import Console

from .config import settings
from .scraper import FlightResult

console = Console()


def _build_message(result: FlightResult, threshold: float) -> str:
    from datetime import date as _date

    pct_below = round((threshold - result.price_usd) / threshold * 100, 1)
    stops_str = "directo" if result.stops == 0 else f"{result.stops} escala{'s' if result.stops > 1 else ''}"
    duration_str = f"{int(result.duration_hours)}h {int((result.duration_hours % 1) * 60)}m"

    ret_origin = result.return_origin or result.destination
    route_str = f"`{result.origin}`→`{result.destination}` + `{ret_origin}`→`{result.origin}`"

    if result.return_date:
        dep = _date.fromisoformat(result.departure_date)
        ret = _date.fromisoformat(result.return_date)
        total_days = (ret - dep).days
        dates_str = (
            f"📅 Salida: {result.departure_date} ({result.origin}→{result.destination})\n"
            f"📅 Vuelta: {result.return_date} ({ret_origin}→{result.origin}) — {total_days} días\n"
        )
    else:
        dates_str = f"📅 Salida: {result.departure_date}\n"

    links_str = ""
    if result.url:
        links_str += f"\n🔗 [Salida — {result.origin}→{result.destination}]({result.url})"
    if result.return_url:
        links_str += f"\n🔗 [Vuelta — {ret_origin}→{result.origin}]({result.return_url})"

    return (
        f"🛫 *OFERTA DE VUELO*\n"
        f"{route_str} | *USD {result.price_usd:,.0f}*\n"
        f"¡{pct_below}% bajo tu umbral de ${threshold:,.0f}!\n\n"
        f"✈️ {result.airline} | {stops_str} | {duration_str}\n"
        f"{dates_str}"
        f"📊 Fuente: {result.source}"
        f"{links_str}"
    )


async def _send_async(message: str) -> None:
    from telegram import Bot

    bot = Bot(token=settings.telegram_bot_token)
    async with bot:
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode="Markdown",
        )


def send_flight_alert(result: FlightResult, threshold: float) -> bool:
    """
    Envía alerta de vuelo por Telegram.

    Returns:
        True si el mensaje fue enviado, False si Telegram no está configurado o falla.
    """
    if not settings.telegram_enabled:
        console.print("[dim]Telegram no configurado — saltando notificación push.[/dim]")
        return False
    try:
        message = _build_message(result, threshold)
        asyncio.run(_send_async(message))
        console.print("[green]✓ Alerta enviada por Telegram.[/green]")
        return True
    except Exception as exc:
        console.print(f"[red]Error enviando Telegram: {exc}[/red]")
        return False
