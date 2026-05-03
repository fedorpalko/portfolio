from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Label, Input, Button, Static, Sparkline
from textual.reactive import reactive
from engine import StrategyParams, UniversalGrowthModel
import numpy as np
import os

class MetricCard(Static):
    def __init__(self, title: str, value: str = "0.0", id: str = None, classes: str = ""):
        super().__init__(id=id, classes=f"metric-card {classes}")
        self.title = title
        self.value_text = value

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="metric-title")
        yield Label(self.value_text, classes="metric-value", id=f"{self.id}-val" if self.id else None)

    def update_value(self, new_value: str, is_positive: bool = None):
        val_label = self.query_one(".metric-value", Label)
        val_label.update(new_value)
        if is_positive is True:
            val_label.set_class(True, "positive")
            val_label.set_class(False, "negative")
        elif is_positive is False:
            val_label.set_class(False, "positive")
            val_label.set_class(True, "negative")

class TradelabApp(App):
    CSS_PATH = "style.css"
    TITLE = "TRADELAB // Strategy Viability"
    
    # Reactive params
    params = reactive(StrategyParams(
        win_rate=0.6,
        reward_ratio=2.0,
        capital=1000.0,
        leverage=1.0,
        sample_size=30,
        std_dev=15.0,
        entry_fee=0.001,
        exit_fee=0.001,
        position_size=0.1
    ))

    BINDINGS = [
        ("up", "focus_previous", "Focus Previous"),
        ("down", "focus_next", "Focus Next"),
        ("k", "apply_kelly", "Apply Kelly Size"),
        ("t", "cycle_theme", "Cycle Theme"),
    ]

    THEMES = ["textual-dark", "textual-light", "nord", "dracula", "monokai"]
    theme_index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("STRATEGY PARAMETERS")
                yield Label("Win Rate (0.0 - 1.0)")
                yield Input(value=str(self.params.win_rate), id="input-win-rate", placeholder="0.6")
                yield Label("Reward:Risk Ratio")
                yield Input(value=str(self.params.reward_ratio), id="input-rr", placeholder="2.0")
                yield Label("Total Capital ($)")
                yield Input(value=str(self.params.capital), id="input-capital", placeholder="1000")
                yield Label("Leverage (x)")
                yield Input(value=str(self.params.leverage), id="input-leverage", placeholder="1.0")
                yield Label("Backtest Sample Size (n)")
                yield Input(value=str(self.params.sample_size), id="input-n", placeholder="30")
                yield Label("P&L Std Dev (σ)")
                yield Input(value=str(self.params.std_dev), id="input-sigma", placeholder="15.0")
                yield Label("Position Size (S, 0-1)")
                yield Input(value=str(self.params.position_size), id="input-s", placeholder="0.1")
                yield Label("Fees (Entry + Exit %)")
                yield Input(value=str(self.params.entry_fee + self.params.exit_fee), id="input-fees", placeholder="0.002")
                
                yield Button("APPLY KELLY SIZE (K)", variant="primary", id="btn-kelly")
                yield Label("\n[Arrow keys to navigate]", classes="metric-title")

            with ScrollableContainer(id="main-content"):
                yield Label("DASHBOARD")
                
                with Horizontal():
                    yield MetricCard("UNIVERSAL GROWTH (G)", id="metric-g")
                    yield MetricCard("KELLY SIZE", id="metric-kelly")
                
                with Horizontal():
                    yield MetricCard("RISK OF RUIN (RoR)", id="metric-ror")
                    yield MetricCard("EXPECTED CAGR", id="metric-cagr")

                yield Static("VIABILITY UNKNOWN", id="viability-badge")
                
                yield Label("EQUITY SIMULATION (SAMPLE PATH)")
                yield Sparkline(id="equity-sparkline")
                
                yield Label("G COMPONENTS BREAKDOWN")
                yield Static("", id="g-breakdown")

        yield Footer()

    def on_mount(self) -> None:
        self.load_params()
        self.run_analysis()

    def action_cycle_theme(self) -> None:
        self.theme_index = (self.theme_index + 1) % len(self.THEMES)
        self.theme = self.THEMES[self.theme_index]
        self.notify(f"Theme: {self.theme}")

    def action_focus_previous(self) -> None:
        self.screen.focus_previous()

    def action_focus_next(self) -> None:
        self.screen.focus_next()

    def action_apply_kelly(self) -> None:
        kelly = UniversalGrowthModel.calculate_kelly(self.params)
        self.query_one("#input-s", Input).value = f"{kelly:.4f}"
        self.update_params_from_inputs()
        self.run_analysis()
        self.save_params()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-kelly":
            self.action_apply_kelly()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Auto-calculate and auto-save on any input change."""
        try:
            self.update_params_from_inputs()
            self.run_analysis()
            self.save_params()
        except Exception:
            pass 

    def update_params_from_inputs(self):
        try:
            win_rate = float(self.query_one("#input-win-rate", Input).value)
            rr = float(self.query_one("#input-rr", Input).value)
            capital = float(self.query_one("#input-capital", Input).value)
            leverage = float(self.query_one("#input-leverage", Input).value)
            n = int(self.query_one("#input-n", Input).value)
            sigma = float(self.query_one("#input-sigma", Input).value)
            fees = float(self.query_one("#input-fees", Input).value)
            s = float(self.query_one("#input-s", Input).value)

            self.params = StrategyParams(
                win_rate=win_rate,
                reward_ratio=rr,
                capital=capital,
                leverage=leverage,
                sample_size=max(1, n),
                std_dev=sigma,
                entry_fee=fees / 2.0,
                exit_fee=fees / 2.0,
                position_size=s
            )
        except (ValueError, TypeError):
            pass

    def run_analysis(self):
        results = UniversalGrowthModel.calculate_g(self.params)
        g_val = results["g_total"]
        
        # Simulation - deeper for better RoR estimation
        sim = UniversalGrowthModel.monte_carlo_simulation(self.params, num_paths=100, num_trades=500)
        ror = sim['ror']

        # Update G Metric
        self.query_one("#metric-g", MetricCard).update_value(
            f"{g_val:.4%}", 
            is_positive=(g_val > 0)
        )
        
        # Update Viability Badge (Viable if G > 0 AND RoR < 5%)
        badge = self.query_one("#viability-badge", Static)
        if g_val > 0 and ror < 0.05:
            badge.update("STRATEGY IS VIABLE")
            badge.set_classes("viable")
        else:
            badge.update("STRATEGY IS NOT VIABLE")
            badge.set_classes("not-viable")

        # Kelly
        kelly = UniversalGrowthModel.calculate_kelly(self.params)
        self.query_one("#metric-kelly", MetricCard).update_value(f"{kelly:.2%}")

        # Breakdown
        breakdown_text = (
            f"G1 (Edge): {results['g1']:.4%}\n"
            f"G2 (Vol Drag): {results['g2']:.4%}\n"
            f"G3 (Uncertainty): {results['g3']:.4%}"
        )
        self.query_one("#g-breakdown", Static).update(breakdown_text)

        # Update RoR Metric
        self.query_one("#metric-ror", MetricCard).update_value(
            f"{ror:.1%}", 
            is_positive=(ror < 0.05)
        )
        
        # CAGR approx from G
        cagr = (1 + g_val)**250 - 1
        self.query_one("#metric-cagr", MetricCard).update_value(f"{cagr:.1%}")

        # Update Sparkline
        sample_path = sim["paths"][0]
        self.query_one("#equity-sparkline", Sparkline).data = sample_path

    def save_params(self):
        # We don't notify on every keystroke to avoid clutter
        try:
            with open("params.json", "w") as f:
                f.write(self.params.to_json())
        except Exception:
            pass

    def load_params(self):
        if os.path.exists("params.json"):
            try:
                with open("params.json", "r") as f:
                    data = f.read()
                    if not data: return
                    self.params = StrategyParams.from_json(data)
                
                # Update fields without triggering notification
                self.query_one("#input-win-rate", Input).value = str(self.params.win_rate)
                self.query_one("#input-rr", Input).value = str(self.params.reward_ratio)
                self.query_one("#input-capital", Input).value = str(self.params.capital)
                self.query_one("#input-leverage", Input).value = str(self.params.leverage)
                self.query_one("#input-n", Input).value = str(self.params.sample_size)
                self.query_one("#input-sigma", Input).value = str(self.params.std_dev)
                self.query_one("#input-s", Input).value = str(self.params.position_size)
                self.query_one("#input-fees", Input).value = str(self.params.entry_fee + self.params.exit_fee)
            except Exception:
                pass

if __name__ == "__main__":
    app = TradelabApp()
    app.run()
