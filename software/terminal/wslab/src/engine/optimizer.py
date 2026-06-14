"""Bayesian (Gaussian-process) optimization via scikit-optimize."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from skopt import gp_minimize
from skopt.space import Integer, Real
from skopt.utils import use_named_args

from engine.backtest import METRIC_KEYS, run_backtest

# Penalty returned to the optimizer for parameter sets that produce no usable
# metric (e.g. a backtest with no trades -> NaN Sharpe). We minimize ``-value``,
# so a large positive number is "very bad".
_PENALTY = 1e6


@dataclass
class OptimizeResult:
    best_params: dict
    best_value: float
    metric: str
    n_calls: int


def optimize(
    data,
    strategy_cls,
    ranges: dict,  # name -> (low, high, is_int)
    metric: str = "Sharpe Ratio",
    n_calls: int = 50,
    cash: float = 10_000,
    commission: float = 0.002,
    fixed_params: dict | None = None,
    on_step: Callable[[int, int, float], None] | None = None,
) -> OptimizeResult:
    """Search ``ranges`` to maximize ``metric`` using GP-based optimization.

    ``ranges`` maps each optimizable parameter to ``(low, high, is_int)``.
    ``on_step(iteration, total, best_so_far)`` is invoked after each evaluation
    so callers can drive a progress bar.
    """
    if not ranges:
        raise ValueError("No optimizable parameters selected.")

    fixed_params = dict(fixed_params or {})
    names = list(ranges)
    dimensions = []
    for name in names:
        low, high, is_int = ranges[name]
        if is_int:
            dimensions.append(Integer(int(low), int(high), name=name))
        else:
            dimensions.append(Real(float(low), float(high), name=name))

    metric_key = METRIC_KEYS.get(metric, metric)
    # Bayesian optimization needs enough samples to fit the surrogate model.
    n_calls = max(int(n_calls), len(dimensions) + 2)

    @use_named_args(dimensions)
    def objective(**params):
        merged = {**fixed_params, **params}
        try:
            result = run_backtest(
                data, strategy_cls, cash=cash, commission=commission, params=merged
            )
            value = float(result.stats.get(metric_key, float("nan")))
        except Exception:
            value = float("nan")
        if value is None or math.isnan(value) or math.isinf(value):
            return _PENALTY
        return -value  # maximize the metric

    state = {"i": 0}

    def _callback(res):
        state["i"] += 1
        if on_step is not None:
            on_step(state["i"], n_calls, -res.fun)

    res = gp_minimize(
        objective,
        dimensions,
        n_calls=n_calls,
        n_initial_points=min(10, n_calls),
        callback=_callback,
        random_state=42,
    )

    best = {
        name: (int(round(val)) if ranges[name][2] else float(val))
        for name, val in zip(names, res.x)
    }
    return OptimizeResult(
        best_params=best,
        best_value=-res.fun,
        metric=metric,
        n_calls=n_calls,
    )
