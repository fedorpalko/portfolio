"""Fincli — an elegant terminal watchlist powered by Yahoo Finance.

Run with:  ./venv/bin/python src/main.py
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import yfinance as yf

# yfinance logs "possibly delisted" warnings straight to the console; mute them
# so they never bleed into Fincli's interface.
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULT_CONFIG = {
    "watchlist": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "refresh_interval": 15,
    "accent_color": "cyan",
    "show_market_cap": True,
}

console = Console()


def load_config() -> dict:
    """Read config.json, filling in any missing keys with defaults."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            console.print("[yellow]Config unreadable — using defaults.[/yellow]")
            data = {}
    else:
        data = {}

    config = {**DEFAULT_CONFIG, **data}
    # Normalise types we depend on.
    config["watchlist"] = [s.upper() for s in config.get("watchlist", [])]
    return config


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #


def humanize(value: float | None) -> str:
    """Compact large numbers, e.g. 2_500_000_000 -> '2.50B'."""
    if value is None:
        return "—"
    for suffix, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= scale:
            return f"{value / scale:.2f}{suffix}"
    return f"{value:,.0f}"


def fetch_quotes(symbols: list[str]) -> dict[str, dict]:
    """Fetch the latest snapshot for each symbol from Yahoo Finance.

    ``fast_info`` is unreliable for live prices, so we derive price and the
    daily change from the last two daily closes and only borrow the static
    fields (currency, share count) from ``fast_info``.
    """
    quotes: dict[str, dict] = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            closes = list(ticker.history(period="2d")["Close"])
            if not closes:
                quotes[symbol] = {"ok": False}
                continue

            price = closes[-1]
            prev = closes[-2] if len(closes) > 1 else None
            change = (price - prev) if prev is not None else None
            pct = (change / prev * 100) if (change is not None and prev) else None

            fi = ticker.fast_info
            shares = fi.get("shares")
            market_cap = fi.get("market_cap") or (
                shares * price if shares else None
            )
            quotes[symbol] = {
                "price": price,
                "change": change,
                "pct": pct,
                "currency": fi.get("currency") or "",
                "market_cap": market_cap,
                "ok": True,
            }
        except Exception:
            quotes[symbol] = {"ok": False}
    return quotes


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def render_table(config: dict, quotes: dict[str, dict]) -> Panel:
    accent = config["accent_color"]
    table = Table(
        expand=True,
        border_style="grey37",
        header_style=f"bold {accent}",
        row_styles=["", "grey7"],
        pad_edge=False,
    )
    table.add_column("Symbol", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")
    if config["show_market_cap"]:
        table.add_column("Mkt Cap", justify="right")

    for symbol in config["watchlist"]:
        q = quotes.get(symbol, {})
        if not q.get("ok"):
            row = [symbol, "[dim]n/a[/dim]", "[dim]—[/dim]", "[dim]—[/dim]"]
            if config["show_market_cap"]:
                row.append("[dim]—[/dim]")
            table.add_row(*row)
            continue

        up = (q["change"] or 0) >= 0
        color = "green" if up else "red"
        arrow = "▲" if up else "▼"
        price = f"{q['price']:,.2f} {q['currency']}".strip()
        change = (
            f"[{color}]{arrow} {q['change']:+,.2f}[/{color}]"
            if q["change"] is not None
            else "—"
        )
        pct = (
            f"[{color}]{q['pct']:+.2f}%[/{color}]" if q["pct"] is not None else "—"
        )
        row = [symbol, price, change, pct]
        if config["show_market_cap"]:
            row.append(humanize(q.get("market_cap")))
        table.add_row(*row)

    stamp = datetime.now().strftime("%H:%M:%S")
    subtitle = (
        f"[dim]updated {stamp}  ·  refresh {config['refresh_interval']}s  ·  "
        f"press Ctrl+C for menu[/dim]"
    )
    return Panel(
        table,
        title=f"[bold {accent}]Fincli[/bold {accent}] [dim]· watchlist[/dim]",
        subtitle=subtitle,
        border_style=accent,
        padding=(1, 2),
    )


def banner(config: dict) -> Panel:
    accent = config["accent_color"]
    art = Text("F I N C L I", style=f"bold {accent}", justify="center")
    tag = Text("Yahoo Finance, in your terminal", style="dim", justify="center")
    return Panel(
        Align.center(Group(art, tag)),
        border_style=accent,
        padding=(1, 4),
    )


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #


def live_view(config: dict) -> None:
    """Auto-refreshing watchlist. Ctrl+C returns to the menu."""
    if not config["watchlist"]:
        console.print("[yellow]Your watchlist is empty. Add a symbol first.[/yellow]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return

    interval = max(1, int(config["refresh_interval"]))
    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while True:
                live.update(
                    Panel(Align.center("[dim]fetching quotes…[/dim]"),
                          border_style=config["accent_color"]),
                    refresh=True,
                )
                quotes = fetch_quotes(config["watchlist"])
                live.update(render_table(config, quotes), refresh=True)
                # Sleep in small slices so Ctrl+C feels responsive.
                for _ in range(interval * 10):
                    time.sleep(0.1)
    except KeyboardInterrupt:
        return


def manage_watchlist(config: dict) -> None:
    accent = config["accent_color"]
    while True:
        console.clear()
        current = ", ".join(config["watchlist"]) or "[dim]empty[/dim]"
        console.print(
            Panel(
                current,
                title=f"[bold {accent}]Watchlist[/bold {accent}]",
                border_style=accent,
                padding=(1, 2),
            )
        )
        console.print("  [bold]a[/bold]  add symbol")
        console.print("  [bold]r[/bold]  remove symbol")
        console.print("  [bold]b[/bold]  back\n")
        choice = Prompt.ask("Choose", choices=["a", "r", "b"], default="b")

        if choice == "a":
            symbol = Prompt.ask("Symbol to add").strip().upper()
            if not symbol:
                continue
            if symbol in config["watchlist"]:
                console.print(f"[yellow]{symbol} is already in the watchlist.[/yellow]")
            else:
                with console.status(f"Verifying {symbol}…"):
                    valid = fetch_quotes([symbol])[symbol].get("ok")
                if valid:
                    config["watchlist"].append(symbol)
                    save_config(config)
                    console.print(f"[green]Added {symbol}.[/green]")
                else:
                    console.print(f"[red]Couldn't find quotes for {symbol}.[/red]")
            time.sleep(0.8)

        elif choice == "r":
            if not config["watchlist"]:
                continue
            symbol = Prompt.ask(
                "Symbol to remove", choices=config["watchlist"], show_choices=True
            )
            config["watchlist"].remove(symbol)
            save_config(config)
            console.print(f"[green]Removed {symbol}.[/green]")
            time.sleep(0.8)

        else:
            return


def edit_settings(config: dict) -> None:
    accent = config["accent_color"]
    while True:
        console.clear()
        table = Table(box=None, padding=(0, 2))
        table.add_column("", style="bold")
        table.add_column("Setting")
        table.add_column("Value", style=accent)
        table.add_row("1", "Refresh interval (s)", str(config["refresh_interval"]))
        table.add_row("2", "Accent color", config["accent_color"])
        table.add_row("3", "Show market cap", str(config["show_market_cap"]))
        console.print(
            Panel(table, title=f"[bold {accent}]Settings[/bold {accent}]",
                  border_style=accent, padding=(1, 2))
        )
        console.print(f"[dim]Editing {CONFIG_PATH}[/dim]\n")
        choice = Prompt.ask("Choose a setting", choices=["1", "2", "3", "b"], default="b")

        if choice == "1":
            value = Prompt.ask("Refresh interval in seconds",
                               default=str(config["refresh_interval"]))
            try:
                config["refresh_interval"] = max(1, int(value))
            except ValueError:
                console.print("[red]Please enter a whole number.[/red]")
                time.sleep(0.8)
                continue
        elif choice == "2":
            config["accent_color"] = Prompt.ask(
                "Accent color",
                choices=["cyan", "magenta", "green", "blue", "yellow", "red"],
                default=config["accent_color"],
            )
            accent = config["accent_color"]
        elif choice == "3":
            config["show_market_cap"] = Confirm.ask(
                "Show market cap column?", default=config["show_market_cap"]
            )
        else:
            return

        save_config(config)
        console.print("[green]Saved.[/green]")
        time.sleep(0.6)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #


def main() -> None:
    config = load_config()
    while True:
        console.clear()
        console.print(banner(config))
        console.print()
        console.print("  [bold]1[/bold]  Live watchlist")
        console.print("  [bold]2[/bold]  Manage watchlist")
        console.print("  [bold]3[/bold]  Settings")
        console.print("  [bold]q[/bold]  Quit\n")
        choice = Prompt.ask("Choose", choices=["1", "2", "3", "q"], default="1")

        if choice == "1":
            live_view(config)
        elif choice == "2":
            manage_watchlist(config)
        elif choice == "3":
            edit_settings(config)
        else:
            console.print(f"[{config['accent_color']}]Goodbye.[/]")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
