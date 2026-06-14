"""WSLAB Textual application.

Single-screen TUI: a sidebar selects between the Backtest, Optimize, Results
and Strategies panels (a ContentSwitcher swaps the main area). Long-running
work — data download, backtests, optimization, charting — runs in thread
workers so the UI stays responsive.
"""

from __future__ import annotations

import webbrowser
from datetime import datetime
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    Select,
    Static,
)

from engine.backtest import run_backtest
from engine.data import DataError, fetch
from engine.optimizer import optimize
from loader import discover

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
STRATEGIES_DIR = ROOT_DIR / "strategies"
OUTPUT_DIR = ROOT_DIR / "output"

# Optimize-metric selector: (label, internal metric name).
METRIC_OPTIONS = [
    ("Sharpe Ratio", "Sharpe Ratio"),
    ("Return %", "Return [%]"),
    ("Max Drawdown %", "Max Drawdown [%]"),
]


def coerce_param(raw: str, default):
    """Coerce a text input to the type of the parameter's default value."""
    raw = (raw or "").strip()
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes", "y", "on")
    if isinstance(default, int):
        return int(float(raw))
    if isinstance(default, float):
        return float(raw)
    return raw


# --------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------
class BacktestPanel(VerticalScroll):
    def __init__(self, strategies: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.strategies = strategies
        self._built_for: str | None = None

    def compose(self) -> ComposeResult:
        first = next(iter(self.strategies), Select.BLANK)
        yield Label("Backtest", classes="panel-title")
        yield Label("Ticker")
        yield Input(value="AAPL", placeholder="AAPL", id="bt-ticker")
        with Horizontal(classes="row"):
            with Vertical():
                yield Label("Start (YYYY-MM-DD)")
                yield Input(value="2020-01-01", id="bt-start")
            with Vertical():
                yield Label("End (YYYY-MM-DD)")
                yield Input(value="2023-01-01", id="bt-end")
        yield Label("Strategy")
        yield Select(
            [(name, name) for name in self.strategies],
            value=first,
            allow_blank=False,
            id="bt-strategy",
        )
        yield Label("Parameters", classes="section")
        yield Vertical(id="bt-params")
        with Horizontal(classes="row"):
            with Vertical():
                yield Label("Cash")
                yield Input(value="10000", id="bt-cash")
            with Vertical():
                yield Label("Commission")
                yield Input(value="0.002", id="bt-commission")
        yield Button("Run Backtest", id="run-backtest", variant="primary")
        yield Static("", id="bt-status", classes="status")

    async def on_mount(self) -> None:
        if self.strategies:
            await self.build_params(next(iter(self.strategies)))

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "bt-strategy" and event.value is not Select.BLANK:
            await self.build_params(event.value)

    async def build_params(self, strat_name: str) -> None:
        if strat_name == self._built_for:
            return
        self._built_for = strat_name
        container = self.query_one("#bt-params", Vertical)
        await container.remove_children()
        cls = self.strategies.get(strat_name)
        if not cls:
            return
        widgets = []
        for pname, default in cls.get_params().items():
            widgets.append(Label(pname))
            widgets.append(Input(value=str(default), id=f"param-{pname}"))
        await container.mount(*widgets)

    def collect(self) -> dict:
        strat = self.query_one("#bt-strategy", Select).value
        if strat is Select.BLANK:
            raise ValueError("Select a strategy.")
        cls = self.strategies[strat]
        params = {
            pname: coerce_param(
                self.query_one(f"#param-{pname}", Input).value, default
            )
            for pname, default in cls.get_params().items()
        }
        return {
            "ticker": self.query_one("#bt-ticker", Input).value.strip(),
            "start": self.query_one("#bt-start", Input).value.strip(),
            "end": self.query_one("#bt-end", Input).value.strip(),
            "strat_name": strat,
            "params": params,
            "cash": float(self.query_one("#bt-cash", Input).value),
            "commission": float(self.query_one("#bt-commission", Input).value),
        }

    def set_status(self, text: str) -> None:
        self.query_one("#bt-status", Static).update(text)


class OptimizePanel(VerticalScroll):
    def __init__(self, strategies: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.strategies = strategies
        self._built_for: str | None = None

    def compose(self) -> ComposeResult:
        first = next(iter(self.strategies), Select.BLANK)
        yield Label("Optimize", classes="panel-title")
        yield Label("Ticker")
        yield Input(value="AAPL", placeholder="AAPL", id="opt-ticker")
        with Horizontal(classes="row"):
            with Vertical():
                yield Label("Start (YYYY-MM-DD)")
                yield Input(value="2020-01-01", id="opt-start")
            with Vertical():
                yield Label("End (YYYY-MM-DD)")
                yield Input(value="2023-01-01", id="opt-end")
        yield Label("Strategy")
        yield Select(
            [(name, name) for name in self.strategies],
            value=first,
            allow_blank=False,
            id="opt-strategy",
        )
        yield Label("Parameter ranges", classes="section")
        yield Vertical(id="opt-params")
        with Horizontal(classes="row"):
            with Vertical():
                yield Label("Metric to maximize")
                yield Select(METRIC_OPTIONS, value="Sharpe Ratio",
                             allow_blank=False, id="opt-metric")
            with Vertical():
                yield Label("Iterations")
                yield Input(value="50", id="opt-iterations")
        with Horizontal(classes="row"):
            with Vertical():
                yield Label("Cash")
                yield Input(value="10000", id="opt-cash")
            with Vertical():
                yield Label("Commission")
                yield Input(value="0.002", id="opt-commission")
        yield Button("Run Optimization", id="run-optimize", variant="primary")
        yield ProgressBar(total=100, show_eta=False, id="opt-progress")
        yield Static("", id="opt-status", classes="status")

    async def on_mount(self) -> None:
        if self.strategies:
            await self.build_params(next(iter(self.strategies)))

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "opt-strategy" and event.value is not Select.BLANK:
            await self.build_params(event.value)

    async def build_params(self, strat_name: str) -> None:
        if strat_name == self._built_for:
            return
        self._built_for = strat_name
        container = self.query_one("#opt-params", Vertical)
        await container.remove_children()
        cls = self.strategies.get(strat_name)
        if not cls:
            return
        widgets = []
        for pname, default in cls.get_params().items():
            if isinstance(default, bool) or not isinstance(default, (int, float)):
                # Non-numeric parameter: held fixed during optimization.
                widgets.append(Label(f"{pname} (fixed)"))
                widgets.append(Input(value=str(default), id=f"optfix-{pname}"))
                continue
            low = max(1, default // 2) if isinstance(default, int) else default / 2
            high = default * 2 if default else 10
            widgets.append(Label(pname))
            row = Horizontal(
                Input(value=str(low), id=f"opt-min-{pname}", classes="range-in"),
                Input(value=str(high), id=f"opt-max-{pname}", classes="range-in"),
                Input(value="1", id=f"opt-step-{pname}", classes="range-in"),
                classes="row",
            )
            widgets.append(row)
        await container.mount(*widgets)

    def collect(self) -> dict:
        strat = self.query_one("#opt-strategy", Select).value
        if strat is Select.BLANK:
            raise ValueError("Select a strategy.")
        cls = self.strategies[strat]
        ranges: dict = {}
        fixed: dict = {}
        for pname, default in cls.get_params().items():
            if isinstance(default, bool) or not isinstance(default, (int, float)):
                fixed[pname] = coerce_param(
                    self.query_one(f"#optfix-{pname}", Input).value, default
                )
                continue
            low = float(self.query_one(f"#opt-min-{pname}", Input).value)
            high = float(self.query_one(f"#opt-max-{pname}", Input).value)
            if low >= high:
                raise ValueError(f"{pname}: min must be less than max.")
            is_int = isinstance(default, int) and not isinstance(default, bool)
            ranges[pname] = (low, high, is_int)
        if not ranges:
            raise ValueError("This strategy has no numeric parameters to optimize.")
        return {
            "ticker": self.query_one("#opt-ticker", Input).value.strip(),
            "start": self.query_one("#opt-start", Input).value.strip(),
            "end": self.query_one("#opt-end", Input).value.strip(),
            "strat_name": strat,
            "ranges": ranges,
            "fixed_params": fixed,
            "metric": self.query_one("#opt-metric", Select).value,
            "n_calls": int(self.query_one("#opt-iterations", Input).value),
            "cash": float(self.query_one("#opt-cash", Input).value),
            "commission": float(self.query_one("#opt-commission", Input).value),
        }

    def set_status(self, text: str) -> None:
        self.query_one("#opt-status", Static).update(text)

    def reset_progress(self, total: int) -> None:
        self.query_one("#opt-progress", ProgressBar).update(total=total, progress=0)

    def advance_progress(self, current: int, total: int) -> None:
        self.query_one("#opt-progress", ProgressBar).update(
            total=total, progress=current
        )


class ResultsPanel(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("Results", classes="panel-title")
        yield Static(
            "Run a backtest or optimization to see results.", id="res-placeholder"
        )
        yield DataTable(id="res-table", zebra_stripes=True, cursor_type="none")
        yield Static("", id="res-best", classes="section")
        with Horizontal(classes="row"):
            yield Button("Open Chart", id="open-chart", disabled=True)
            yield Button("Run with Best Params", id="run-best", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#res-table", DataTable)
        table.add_columns("Metric", "Value")

    def show(self, summary, best_text: str = "", enable_best: bool = False) -> None:
        self.query_one("#res-placeholder", Static).display = False
        table = self.query_one("#res-table", DataTable)
        table.clear()
        for label, value in summary:
            table.add_row(label, value)
        self.query_one("#res-best", Static).update(best_text)
        self.query_one("#open-chart", Button).disabled = False
        self.query_one("#run-best", Button).disabled = not enable_best


class StrategiesPanel(VerticalScroll):
    def __init__(self, strategies: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.strategies = strategies

    def compose(self) -> ComposeResult:
        yield Label("Strategies", classes="panel-title")
        for name, cls in self.strategies.items():
            params = cls.get_params()
            param_text = (
                ", ".join(f"{k}={v}" for k, v in params.items()) or "(none)"
            )
            body = (
                f"[b]{name}[/b]\n"
                f"{cls.description()}\n"
                f"[dim]Parameters:[/dim] {param_text}"
            )
            yield Static(body, classes="strategy-card")
        yield Static(
            "[b]Add your own[/b]\n"
            "Drop a [i].py[/i] file into the [i]strategies/[/i] folder. Inherit "
            "from [i]WSlabStrategy[/i] (import it with "
            "[i]from wslab.strategy import WSlabStrategy[/i]), declare parameters "
            "as class attributes, and implement [i]longSignal()[/i] and "
            "[i]shortSignal()[/i]. It is auto-discovered on next launch.",
            classes="strategy-card",
        )


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class WSlabApp(App):
    TITLE = "WSLAB — Wall Street Lab"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("b", "nav('backtest')", "Backtest"),
        ("o", "nav('optimize')", "Optimize"),
        ("r", "nav('results')", "Results"),
        ("s", "nav('strategies')", "Strategies"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.strategies = discover(STRATEGIES_DIR)
        self.last_result = None
        self.best_config: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Button("Backtest", id="nav-backtest")
                yield Button("Optimize", id="nav-optimize")
                yield Button("Results", id="nav-results")
                yield Button("Strategies", id="nav-strategies")
            with ContentSwitcher(initial="backtest", id="content"):
                yield BacktestPanel(self.strategies, id="backtest")
                yield OptimizePanel(self.strategies, id="optimize")
                yield ResultsPanel(id="results")
                yield StrategiesPanel(self.strategies, id="strategies")
        yield Footer()

    # -- navigation --------------------------------------------------------
    def action_nav(self, target: str) -> None:
        self.query_one("#content", ContentSwitcher).current = target

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("nav-"):
            self.action_nav(bid[len("nav-"):])
        elif bid == "run-backtest":
            self._start_backtest()
        elif bid == "run-optimize":
            self._start_optimize()
        elif bid == "open-chart":
            self._open_chart()
        elif bid == "run-best":
            self._run_best()

    # -- backtest ----------------------------------------------------------
    def _start_backtest(self) -> None:
        panel = self.query_one(BacktestPanel)
        try:
            cfg = panel.collect()
        except (ValueError, KeyError) as exc:
            panel.set_status(f"[red]Invalid input:[/] {exc}")
            return
        panel.set_status("Running…")
        self._backtest_worker(cfg, from_best=False)

    def _run_best(self) -> None:
        if not self.best_config:
            return
        self.query_one(BacktestPanel).set_status("")
        self._backtest_worker(self.best_config, from_best=True)

    @work(thread=True, exclusive=True, group="run")
    def _backtest_worker(self, cfg: dict, from_best: bool) -> None:
        panel = self.query_one(BacktestPanel)
        try:
            self.call_from_thread(panel.set_status, "Fetching data…")
            data = fetch(cfg["ticker"], cfg["start"], cfg["end"])
            cls = self.strategies[cfg["strat_name"]]
            self.call_from_thread(panel.set_status, "Running backtest…")
            result = run_backtest(
                data, cls,
                cash=cfg["cash"], commission=cfg["commission"],
                params=cfg["params"],
            )
        except (DataError, ValueError, KeyError) as exc:
            self.call_from_thread(panel.set_status, f"[red]Error:[/] {exc}")
            return
        except Exception as exc:  # backtesting.py / data edge cases
            self.call_from_thread(panel.set_status, f"[red]Backtest failed:[/] {exc}")
            return

        self.last_result = result
        best_text = self._format_best(cfg["params"]) if from_best else ""
        self.call_from_thread(panel.set_status, "[green]Done.[/]")
        self.call_from_thread(
            self.query_one(ResultsPanel).show, result.summary(), best_text, False
        )
        self.call_from_thread(self.action_nav, "results")

    # -- optimize ----------------------------------------------------------
    def _start_optimize(self) -> None:
        panel = self.query_one(OptimizePanel)
        try:
            cfg = panel.collect()
        except (ValueError, KeyError) as exc:
            panel.set_status(f"[red]Invalid input:[/] {exc}")
            return
        panel.set_status("Starting optimization…")
        panel.reset_progress(cfg["n_calls"])
        self._optimize_worker(cfg)

    @work(thread=True, exclusive=True, group="run")
    def _optimize_worker(self, cfg: dict) -> None:
        panel = self.query_one(OptimizePanel)
        try:
            self.call_from_thread(panel.set_status, "Fetching data…")
            data = fetch(cfg["ticker"], cfg["start"], cfg["end"])
            cls = self.strategies[cfg["strat_name"]]

            def on_step(i: int, total: int, best: float) -> None:
                self.call_from_thread(panel.advance_progress, i, total)
                self.call_from_thread(
                    panel.set_status,
                    f"Iteration {i}/{total} — best {cfg['metric']}: {best:,.3f}",
                )

            opt = optimize(
                data, cls,
                ranges=cfg["ranges"], metric=cfg["metric"],
                n_calls=cfg["n_calls"], cash=cfg["cash"],
                commission=cfg["commission"], fixed_params=cfg["fixed_params"],
                on_step=on_step,
            )
            best_params = {**cfg["fixed_params"], **opt.best_params}
            result = run_backtest(
                data, cls,
                cash=cfg["cash"], commission=cfg["commission"], params=best_params,
            )
        except (DataError, ValueError, KeyError) as exc:
            self.call_from_thread(panel.set_status, f"[red]Error:[/] {exc}")
            return
        except Exception as exc:
            self.call_from_thread(panel.set_status, f"[red]Optimization failed:[/] {exc}")
            return

        self.last_result = result
        self.best_config = {
            "ticker": cfg["ticker"], "start": cfg["start"], "end": cfg["end"],
            "strat_name": cfg["strat_name"], "params": best_params,
            "cash": cfg["cash"], "commission": cfg["commission"],
        }
        best_text = (
            f"[b]Best parameters[/b] (max {opt.metric} = {opt.best_value:,.3f})\n"
            + self._format_best(opt.best_params)
        )
        self.call_from_thread(panel.set_status, "[green]Optimization complete.[/]")
        self.call_from_thread(
            self.query_one(ResultsPanel).show, result.summary(), best_text, True
        )
        self.call_from_thread(self.action_nav, "results")

    @staticmethod
    def _format_best(params: dict) -> str:
        return ", ".join(f"{k}={v}" for k, v in params.items())

    # -- charting ----------------------------------------------------------
    def _open_chart(self) -> None:
        if self.last_result is None:
            self.notify("No backtest to chart yet.", severity="warning")
            return
        self.notify("Generating chart…")
        self._chart_worker()

    @work(thread=True, exclusive=True, group="chart")
    def _chart_worker(self) -> None:
        result = self.last_result
        if result is None:
            return
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = OUTPUT_DIR / f"chart_{stamp}.html"
            result.bt.plot(filename=str(path), open_browser=False)
            webbrowser.open(f"file://{path}")
            self.call_from_thread(
                self.notify, f"Chart saved to output/{path.name}"
            )
        except Exception as exc:
            self.call_from_thread(
                self.notify, f"Chart failed: {exc}", severity="error"
            )


if __name__ == "__main__":
    WSlabApp().run()
