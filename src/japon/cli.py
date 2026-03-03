"""CLI principal — entry point `japon` via Typer."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="japon",
    help="Planificador de viaje Japón 2027 — monitor de vuelos BUE → TYO",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
flights_app = typer.Typer(help="Comandos de vuelos y precios.", no_args_is_help=True)
app.add_typer(flights_app, name="flights")

console = Console()


# ─── japon flights check ──────────────────────────────────────────────────────

@flights_app.command("check")
def flights_check(
    date: Annotated[
        Optional[str],
        typer.Option("--date", "-d", help="Mes objetivo YYYY-MM (ej: 2027-02)"),
    ] = None,
    threshold: Annotated[
        Optional[float],
        typer.Option("--threshold", "-t", help="Umbral de precio USD"),
    ] = None,
    top: Annotated[
        int,
        typer.Option("--top", "-n", help="Mostrar N mejores resultados"),
    ] = 10,
) -> None:
    """Consulta los mejores precios BUE → TYO ahora mismo."""
    from .alerts import evaluate_and_dispatch
    from .config import settings
    from .history import append_results
    from .scraper import fetch_best_prices

    console.print(f"\n[bold]Buscando vuelos[/bold] {settings.origin_iata} → {', '.join(settings.destinations)}…\n")
    results = fetch_best_prices(year_month=date)

    if not results:
        console.print("[red]No se encontraron resultados. Verificar conexión o configuración.[/red]")
        raise typer.Exit(1)

    append_results(results)

    # Tabla de mejores opciones
    table = Table(title=f"Top {top} vuelos — precio combinado (salida + vuelta)", show_lines=True)
    table.add_column("Salida", style="white")
    table.add_column("Vuelta", style="white")
    table.add_column("Días", justify="center", style="dim")
    table.add_column("Ruta ida", style="cyan")
    table.add_column("Ruta vuelta", style="cyan")
    table.add_column("Precio USD", style="bold green", justify="right")
    table.add_column("Aerolínea", style="white")
    table.add_column("Fuente", style="dim")

    for r in results[:top]:
        ret_origin = r.return_origin or r.destination
        total_days = ""
        if r.return_date:
            import datetime as _dt
            d = (_dt.date.fromisoformat(r.return_date) - _dt.date.fromisoformat(r.departure_date)).days
            total_days = str(d)
        table.add_row(
            r.departure_date,
            r.return_date,
            total_days,
            f"{r.origin}→{r.destination}",
            f"{ret_origin}→{r.origin}",
            f"${r.price_usd:,.0f}",
            r.airline,
            r.source,
        )

    console.print(table)

    # Links del vuelo más barato
    best = results[0]
    ret_origin = best.return_origin or best.destination
    if best.url:
        console.print(f"\n[bold]🔗 Salida ({best.origin}→{best.destination}):[/bold] {best.url}")
    if best.return_url:
        console.print(f"[bold]🔗 Vuelta ({ret_origin}→{best.origin}):[/bold] {best.return_url}\n")

    evaluate_and_dispatch(results, threshold)


# ─── japon flights monitor ────────────────────────────────────────────────────

@flights_app.command("monitor")
def flights_monitor(
    interval: Annotated[
        Optional[int],
        typer.Option("--interval", "-i", help="Intervalo en minutos entre chequeos"),
    ] = None,
    threshold: Annotated[
        Optional[float],
        typer.Option("--threshold", "-t", help="Umbral de precio USD para alertar"),
    ] = None,
    date: Annotated[
        Optional[str],
        typer.Option("--date", "-d", help="Mes objetivo YYYY-MM"),
    ] = None,
) -> None:
    """Inicia monitoreo periódico de precios (Ctrl+C para detener)."""
    from .monitor import start_monitor

    start_monitor(interval_minutes=interval, threshold=threshold, year_month=date)


# ─── japon flights history ────────────────────────────────────────────────────

@flights_app.command("history")
def flights_history(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Últimos N registros a mostrar"),
    ] = 20,
) -> None:
    """Muestra el historial de precios guardados."""
    from .history import get_cheapest_ever, get_recent

    records = get_recent(limit)
    if not records:
        console.print("[yellow]Sin historial aún. Ejecuta `japon flights check` primero.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Historial — últimos {len(records)} registros", show_lines=True)
    table.add_column("Chequeado", style="dim")
    table.add_column("Salida", style="white")
    table.add_column("Vuelta", style="white")
    table.add_column("Ruta ida", style="cyan")
    table.add_column("Vuelta desde", style="cyan")
    table.add_column("Precio USD", style="bold green", justify="right")
    table.add_column("Fuente", style="dim")

    for r in records:
        ret_orig = r.get("return_origin", "—") or "—"
        dest = r.get("destination", "?")
        origin = r.get("origin", "?")
        ret_route = f"{ret_orig}→{origin}" if ret_orig != "—" else "—"
        table.add_row(
            r["checked_at"][:19].replace("T", " "),
            r["departure_date"],
            r.get("return_date", "—"),
            f"{origin}→{dest}",
            ret_route,
            f"${r['price_usd']:,.0f}",
            r["source"],
        )

    console.print(table)

    cheapest = get_cheapest_ever()
    if cheapest:
        console.print(
            f"\n[bold]Mínimo histórico:[/bold] "
            f"[green]USD {cheapest['price_usd']:,.0f}[/green] "
            f"({cheapest['origin']}→{cheapest['destination']} "
            f"{cheapest['departure_date']} — {cheapest['airline']})"
        )


# ─── japon flights alert set ──────────────────────────────────────────────────

@flights_app.command("alert")
def flights_alert(
    action: Annotated[str, typer.Argument(help="Acción: 'set'")],
    value: Annotated[float, typer.Argument(help="Nuevo umbral en USD")],
) -> None:
    """Cambia el umbral de alerta en .env."""
    from .config import PROJECT_ROOT

    if action != "set":
        console.print(f"[red]Acción desconocida: {action}. Usa 'set'.[/red]")
        raise typer.Exit(1)

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        console.print("[red].env no encontrado. Ejecuta `japon setup` primero.[/red]")
        raise typer.Exit(1)

    content = env_file.read_text(encoding="utf-8")
    new_line = f"FLIGHT_PRICE_THRESHOLD_USD={value:.0f}"

    if "FLIGHT_PRICE_THRESHOLD_USD=" in content:
        import re
        content = re.sub(r"FLIGHT_PRICE_THRESHOLD_USD=\S*", new_line, content)
    else:
        content += f"\n{new_line}\n"

    env_file.write_text(content, encoding="utf-8")
    console.print(f"[green]✓ Umbral actualizado a USD {value:,.0f}[/green]")


# ─── japon setup ─────────────────────────────────────────────────────────────

@app.command("setup")
def setup() -> None:
    """Wizard de configuración inicial — crea .env desde .env.example."""
    from .config import PROJECT_ROOT

    env_example = PROJECT_ROOT / ".env.example"
    env_file = PROJECT_ROOT / ".env"

    if env_file.exists():
        overwrite = typer.confirm(".env ya existe. ¿Sobreescribir?", default=False)
        if not overwrite:
            console.print("[yellow]Setup cancelado.[/yellow]")
            raise typer.Exit()

    content = env_example.read_text(encoding="utf-8")

    console.print("\n[bold]Configuración de Japón Bot[/bold]\n")
    console.print("[dim]Presiona Enter para dejar un campo vacío.[/dim]\n")

    fields = {
        "TELEGRAM_BOT_TOKEN": "Token del bot de Telegram (BotFather)",
        "TELEGRAM_CHAT_ID": "Chat ID de Telegram",
        "AMADEUS_API_KEY": "Amadeus API Key (opcional)",
        "AMADEUS_API_SECRET": "Amadeus API Secret (opcional)",
        "FLIGHT_PRICE_THRESHOLD_USD": "Umbral de precio en USD",
        "MONITOR_INTERVAL_MINUTES": "Intervalo de monitoreo en minutos",
    }

    for key, label in fields.items():
        value = typer.prompt(f"  {label}", default="", show_default=False)
        if value:
            import re
            content = re.sub(rf"{key}=\S*", f"{key}={value}", content)

    env_file.write_text(content, encoding="utf-8")
    console.print(f"\n[green]✓ .env creado en {env_file}[/green]")
    console.print("[dim]Ejecuta `uv run japon flights check` para probar.[/dim]\n")


if __name__ == "__main__":
    app()
