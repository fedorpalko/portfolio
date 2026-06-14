"""Example custom strategy.

Drop files like this one into the top-level ``strategies/`` folder and WSLAB
will auto-discover them at startup. Inherit from ``WSlabStrategy``, declare
parameters as class attributes, and implement ``longSignal`` / ``shortSignal``.
"""

from wslab.strategy import WSlabStrategy

from engine import indicators


class RsiReversion(WSlabStrategy):
    """RSI mean reversion.

    Goes long when RSI falls below the oversold threshold and short when it
    rises above the overbought threshold.
    """

    name = "RSI Reversion"

    period = 14
    oversold = 30
    overbought = 70

    def init(self):
        self.rsi = self.I(indicators.rsi, self.data.Close, self.period)

    def longSignal(self) -> bool:
        return self.rsi[-1] < self.oversold

    def shortSignal(self) -> bool:
        return self.rsi[-1] > self.overbought
