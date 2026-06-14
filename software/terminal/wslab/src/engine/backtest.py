"""Backtest execution wrapped around backtesting.py."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from backtesting import Backtest

# Friendly label -> backtesting.py stats key.
METRIC_KEYS = {
    "Return [%]": "Return [%]",
    "Sharpe Ratio": "Sharpe Ratio",
    "Max Drawdown [%]": "Max. Drawdown [%]",
    "Win Rate [%]": "Win Rate [%]",
    "# Trades": "# Trades",
    "Profit Factor": "Profit Factor",
}


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if math.isnan(value):
            return "—"
        return f"{value:,.2f}"
    return str(value)


@dataclass
class BacktestResult:
    stats: pd.Series
    bt: Backtest
    params: dict = field(default_factory=dict)

    def metric(self, label: str):
        return self.stats.get(METRIC_KEYS.get(label, label), float("nan"))

    def summary(self) -> list[tuple[str, str]]:
        return [(label, _fmt(self.metric(label))) for label in METRIC_KEYS]


def run_backtest(
    data,
    strategy_cls,
    cash: float = 10_000,
    commission: float = 0.002,
    params: dict | None = None,
) -> BacktestResult:
    params = params or {}
    try:
        # finalize_trades closes positions open at the end so they count in the
        # stats. Added in newer backtesting.py; fall back if unsupported.
        bt = Backtest(
            data, strategy_cls, cash=cash, commission=commission,
            finalize_trades=True,
        )
    except TypeError:
        bt = Backtest(data, strategy_cls, cash=cash, commission=commission)
    stats = bt.run(**params)
    return BacktestResult(stats=stats, bt=bt, params=dict(params))
