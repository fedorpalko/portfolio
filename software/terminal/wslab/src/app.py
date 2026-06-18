"""WSLAB console application (Rich).

A menu-driven interactive terminal app built with Rich. The main loop offers
Backtest / Optimize / Results / Strategies actions; each walks the user through
prompts, runs the work, and renders results as Rich tables and panels. The
engine, strategy and optimization layers are UI-agnostic and shared as-is.
"""

from __future__ import annotations

import webbrowser
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from engine.backtest import run_backtest
from engine.data import VALID_INTERVALS, DataError, check_interval, fetch
from engine.optimizer import optimize
from loader import discover

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
STRATEGIES_DIR = ROOT_DIR / "strategies"
OUTPUT_DIR = ROOT_DIR / "output"

# Optimize-metric selector: label -> internal metric name.
METRIC_OPTIONS = {
    "Sharpe Ratio": "Sharpe Ratio",
    "Return %": "Return [%]",
    "Max Drawdown %": "Max Drawdown [%]",
}


class WSlabApp:
    def __init__(self) -> None:
        self.console = Console()
        self.strategies = discover(STRATEGIES_DIR)
        self.last_result = None
        self.best_config: dict | None = None

    # -- entry point -------------------------------------------------------
    def run(self) -> None:
        self.console.clear()
        self._print_header()
        actions = {
            "b": self.do_backtest,
            "o": self.do_optimize,
            "r": self.do_results,
            "s": self.do_strategies,
        }
        while True:
            self._print_menu()
            choice = Prompt.ask(
                "[bold]Select[/]",
                choices=["b", "o", "r", "s", "q"],
                default="b",
            )
            if choice == "q":
                break
            self.console.print()
            try:
                actions[choice]()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Cancelled.[/]")
        self.console.print("\n[bold cyan]Goodbye.[/]")

    # -- chrome ------------------------------------------------------------
    def _print_header(self) -> None:
        title = Text("WSLAB — Wall Street Lab", style="bold green", justify="center")
        subtitle = Text(
            "TUI backtesting & Bayesian optimization · not for live trading",
            style="dim",
            justify="center",
        )
        self.console.print(
            Panel(Text.assemble(title, "\n", subtitle), box=box.DOUBLE,
                  border_style="green")
        )

    def _print_menu(self) -> None:
        menu = Table.grid(padding=(0, 2))
        menu.add_column(style="bold cyan")
        menu.add_column()
        menu.add_row("b", "Backtest a strategy")
        menu.add_row("o", "Optimize parameters (Bayesian)")
        menu.add_row("r", "View last results")
        menu.add_row("s", "Browse strategies")
        menu.add_row("q", "Quit")
        self.console.print(Panel(menu, title="Menu", border_style="blue",
                                 box=box.ROUNDED, expand=False))

    # -- shared prompts ----------------------------------------------------
    def _choose_strategy(self) -> str | None:
        names = list(self.strategies)
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Strategy")
        for i, name in enumerate(names, 1):
            table.add_row(str(i), name)
        self.console.print(table)
        idx = IntPrompt.ask("Strategy #", choices=[str(i) for i in range(1, len(names) + 1)],
                            default=1)
        return names[idx - 1]

    def _prompt_value(self, label: str, default):
        """Prompt for a single typed value matching ``default``'s type."""
        if isinstance(default, bool):
            return Confirm.ask(label, default=default)
        if isinstance(default, int):
            return IntPrompt.ask(label, default=default)
        if isinstance(default, float):
            return FloatPrompt.ask(label, default=default)
        return Prompt.ask(label, default=str(default))

    def _prompt_common(self) -> dict:
        ticker = Prompt.ask("Ticker", default="AAPL").strip().upper()
        start = Prompt.ask("Start date (YYYY-MM-DD)", default="2020-01-01").strip()
        end = Prompt.ask("End date (YYYY-MM-DD)", default="2023-01-01").strip()
        interval = self._prompt_interval(start, end)
        return {"ticker": ticker, "start": start, "end": end, "interval": interval}

    def _prompt_interval(self, start: str, end: str) -> str:
        """Prompt for a chart interval, re-asking until it's valid for the range.

        yfinance caps how far back intraday bars go (and how wide a 1m request
        can be), so a bad pairing is rejected with an explanation rather than
        left to fail at download time.
        """
        self.console.print(
            "[dim]Chart interval — intraday bars have limited history: "
            "1m ≤7d & ~30d back · 2m–90m ~60d back · 60m/1h ~730d back · "
            "1d and coarser unlimited.[/]"
        )
        while True:
            interval = Prompt.ask("Interval", choices=VALID_INTERVALS, default="1d")
            warning = check_interval(start, end, interval)
            if warning is None:
                return interval
            self.console.print(Panel(
                warning, title="⚠  That interval won't work for this range",
                border_style="red", box=box.ROUNDED, expand=False,
            ))
            self.console.print("[yellow]Pick another interval.[/]")

    # -- backtest ----------------------------------------------------------
    def do_backtest(self, preset: dict | None = None) -> None:
        if preset is None:
            common = self._prompt_common()
            strat_name = self._choose_strategy()
            cls = self.strategies[strat_name]
            self.console.print("[dim]Strategy parameters:[/]")
            params = {
                pname: self._prompt_value(f"  {pname}", default)
                for pname, default in cls.get_params().items()
            }
            cash = FloatPrompt.ask("Cash", default=10000.0)
            commission = FloatPrompt.ask("Commission", default=0.002)
            cfg = {**common, "strat_name": strat_name, "params": params,
                   "cash": cash, "commission": commission}
        else:
            cfg = preset

        interval = cfg.get("interval", "1d")
        try:
            with self.console.status(f"Fetching {interval} data…", spinner="dots"):
                data = fetch(cfg["ticker"], cfg["start"], cfg["end"], interval=interval)
            cls = self.strategies[cfg["strat_name"]]
            with self.console.status("Running backtest…", spinner="dots"):
                result = run_backtest(
                    data, cls, cash=cfg["cash"], commission=cfg["commission"],
                    params=cfg["params"],
                )
        except DataError as exc:
            self.console.print(f"[red]Data error:[/] {exc}")
            return
        except Exception as exc:
            self.console.print(f"[red]Backtest failed:[/] {exc}")
            return

        self.last_result = result
        self._show_result(result)
        self._maybe_open_chart()

    # -- optimize ----------------------------------------------------------
    def do_optimize(self) -> None:
        common = self._prompt_common()
        strat_name = self._choose_strategy()
        cls = self.strategies[strat_name]

        ranges: dict = {}
        fixed: dict = {}
        self.console.print("[dim]Parameter ranges (numeric params are optimized):[/]")
        for pname, default in cls.get_params().items():
            if isinstance(default, bool) or not isinstance(default, (int, float)):
                fixed[pname] = self._prompt_value(f"  {pname} (fixed)", default)
                continue
            is_int = isinstance(default, int)
            lo_default = max(1, default // 2) if is_int else default / 2
            hi_default = default * 2 if default else 10
            ask = IntPrompt.ask if is_int else FloatPrompt.ask
            low = ask(f"  {pname} min", default=lo_default)
            high = ask(f"  {pname} max", default=hi_default)
            if low >= high:
                self.console.print(f"[red]{pname}: min must be less than max.[/]")
                return
            ranges[pname] = (low, high, is_int)

        if not ranges:
            self.console.print("[red]This strategy has no numeric parameters to optimize.[/]")
            return

        metric_label = Prompt.ask("Metric to maximize",
                                  choices=list(METRIC_OPTIONS), default="Sharpe Ratio")
        metric = METRIC_OPTIONS[metric_label]
        n_calls = IntPrompt.ask("Iterations", default=50)

        interval = common.get("interval", "1d")
        try:
            with self.console.status(f"Fetching {interval} data…", spinner="dots"):
                data = fetch(common["ticker"], common["start"], common["end"],
                             interval=interval)

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Optimizing ({metric_label})", total=n_calls)

                def on_step(i: int, total: int, best: float) -> None:
                    progress.update(task, completed=i, total=total,
                                    description=f"best {metric_label}: {best:,.3f}")

                opt = optimize(
                    data, cls, ranges=ranges, metric=metric, n_calls=n_calls,
                    cash=10000.0, commission=0.002, fixed_params=fixed,
                    on_step=on_step,
                )

            best_params = {**fixed, **opt.best_params}
            with self.console.status("Backtesting best parameters…", spinner="dots"):
                result = run_backtest(data, cls, cash=10000.0, commission=0.002,
                                      params=best_params)
        except DataError as exc:
            self.console.print(f"[red]Data error:[/] {exc}")
            return
        except Exception as exc:
            self.console.print(f"[red]Optimization failed:[/] {exc}")
            return

        self.last_result = result
        self.best_config = {**common, "strat_name": strat_name,
                            "params": best_params, "cash": 10000.0,
                            "commission": 0.002}

        best_table = Table(box=box.SIMPLE, show_header=False)
        best_table.add_column("Parameter", style="cyan")
        best_table.add_column("Value", style="bold")
        for k, v in opt.best_params.items():
            best_table.add_row(k, str(v))
        self.console.print(Panel(
            best_table,
            title=f"Best parameters (max {opt.metric} = {opt.best_value:,.3f})",
            border_style="green", box=box.ROUNDED, expand=False,
        ))
        self._show_result(result)

        if Confirm.ask("Run a fresh backtest with these parameters?", default=False):
            self.do_backtest(preset=self.best_config)
        else:
            self._maybe_open_chart()

    # -- results -----------------------------------------------------------
    def do_results(self) -> None:
        if self.last_result is None:
            self.console.print("[yellow]No results yet. Run a backtest or optimization first.[/]")
            return
        self._show_result(self.last_result)
        self._maybe_open_chart()

    def _show_result(self, result) -> None:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        for label, value in result.summary():
            table.add_row(label, value)
        self.console.print(Panel(table, title="Results", border_style="magenta",
                                 expand=False))

    # -- strategies --------------------------------------------------------
    def do_strategies(self) -> None:
        for name, cls in self.strategies.items():
            params = cls.get_params()
            param_text = ", ".join(f"{k}={v}" for k, v in params.items()) or "(none)"
            body = Text.assemble(
                (cls.description() + "\n\n", ""),
                ("Parameters: ", "dim"),
                (param_text, "cyan"),
            )
            self.console.print(Panel(body, title=name, border_style="blue",
                                     box=box.ROUNDED))
        self.console.print(Panel(
            "Drop a .py file into the strategies/ folder. Inherit from "
            "WSlabStrategy (from wslab.strategy import WSlabStrategy), declare "
            "parameters as class attributes, and implement longSignal() and "
            "shortSignal(). It is auto-discovered on next launch.",
            title="Add your own", border_style="green", box=box.ROUNDED,
        ))

    # -- charting ----------------------------------------------------------
    def _maybe_open_chart(self) -> None:
        if self.last_result is None:
            return
        if Confirm.ask("Open the interactive HTML chart in your browser?",
                       default=False):
            self._open_chart()

    def _open_chart(self) -> None:
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = OUTPUT_DIR / f"chart_{stamp}.html"
            with self.console.status("Generating chart…", spinner="dots"):
                self.last_result.bt.plot(filename=str(path), open_browser=False)
            webbrowser.open(f"file://{path}")
            self.console.print(f"[green]Chart saved to[/] output/{path.name}")
        except Exception as exc:
            self.console.print(f"[red]Chart failed:[/] {exc}")


if __name__ == "__main__":
    WSlabApp().run()
