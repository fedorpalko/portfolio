"""Built-in strategy: moving-average crossover."""

from __future__ import annotations

from backtesting.lib import crossover

from engine import indicators
from strategies.base import WSlabStrategy


class SmaEmaCrossover(WSlabStrategy):
    """Moving-average crossover.

    Goes long when the fast moving average crosses above the slow one and
    short when it crosses below. Works with either simple (SMA) or exponential
    (EMA) moving averages via the ``ma_type`` parameter.
    """

    name = "SMA/EMA Crossover"

    fast_period = 10
    slow_period = 30
    ma_type = "SMA"  # "SMA" or "EMA"

    def init(self):
        close = self.data.Close
        self.fast_ma = self.I(indicators.ma, close, self.fast_period, self.ma_type)
        self.slow_ma = self.I(indicators.ma, close, self.slow_period, self.ma_type)

    def longSignal(self) -> bool:
        return crossover(self.fast_ma, self.slow_ma)

    def shortSignal(self) -> bool:
        return crossover(self.slow_ma, self.fast_ma)
