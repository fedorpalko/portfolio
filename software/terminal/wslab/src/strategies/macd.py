"""Built-in strategy: MACD crossover."""

from __future__ import annotations

from backtesting.lib import crossover

from engine import indicators
from strategies.base import WSlabStrategy


class MacdCrossover(WSlabStrategy):
    """MACD crossover.

    Goes long when the MACD line crosses above its signal line and short when
    it crosses below.
    """

    name = "MACD"

    fast = 12
    slow = 26
    signal = 9

    def init(self):
        close = self.data.Close
        self.macd_line, self.signal_line = self.I(
            indicators.macd, close, self.fast, self.slow, self.signal
        )

    def longSignal(self) -> bool:
        return crossover(self.macd_line, self.signal_line)

    def shortSignal(self) -> bool:
        return crossover(self.signal_line, self.macd_line)
