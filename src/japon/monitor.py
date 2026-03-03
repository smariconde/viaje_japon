"""Loop de monitoreo periódico con APScheduler."""

from __future__ import annotations

import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from rich.console import Console

from .alerts import evaluate_and_dispatch
from .config import settings
from .history import append_results
from .scraper import fetch_best_prices

console = Console()


def _run_check(year_month: str | None, threshold: float) -> None:
    """Ejecuta un ciclo completo: scraping → historial → alertas."""
    console.print(
        f"\n[bold blue]── Chequeando vuelos {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ──[/bold blue]"
    )
    results = fetch_best_prices(year_month=year_month)
    if results:
        append_results(results)
    evaluate_and_dispatch(results, threshold)


def start_monitor(
    interval_minutes: int | None = None,
    threshold: float | None = None,
    year_month: str | None = None,
) -> None:
    """
    Inicia el loop de monitoreo. Bloquea hasta que se recibe SIGINT/SIGTERM.

    Args:
        interval_minutes: Frecuencia de chequeo. Default: settings.monitor_interval_minutes.
        threshold:        Umbral de precio en USD. Default: settings.flight_price_threshold_usd.
        year_month:       Mes objetivo YYYY-MM. Default: primer mes en settings.
    """
    active_interval = interval_minutes or settings.monitor_interval_minutes
    active_threshold = threshold if threshold is not None else settings.flight_price_threshold_usd

    console.print(
        f"[bold green]Monitor iniciado[/bold green] — "
        f"chequeo cada [cyan]{active_interval}[/cyan] min | "
        f"umbral [cyan]USD {active_threshold:,.0f}[/cyan]\n"
        f"[dim]Presiona Ctrl+C para detener.[/dim]\n"
    )

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_check,
        trigger="interval",
        minutes=active_interval,
        args=[year_month, active_threshold],
        next_run_time=datetime.now(),  # ejecutar inmediatamente al iniciar
    )

    def _shutdown(signum, frame):
        console.print("\n[yellow]Deteniendo monitor...[/yellow]")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("[yellow]Monitor detenido.[/yellow]")
