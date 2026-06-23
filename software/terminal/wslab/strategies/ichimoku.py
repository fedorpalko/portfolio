"""Custom strategy: Ichimoku Kinko Hyo (cloud) trend following.

Drop-in WSLAB strategy. Inherits from ``WSlabStrategy``, declares the Ichimoku
periods as optimizable class attributes, and implements ``longSignal`` /
``shortSignal``.
"""

from wslab.strategy import WSlabStrategy

from engine import indicators


class Ichimoku(WSlabStrategy):
    """Ichimoku cloud trend following.

    Goes long while the Tenkan-sen sits above the Kijun-sen and price is above
    the cloud (both Senkou spans), and short on the mirror condition with price
    below the cloud. The cloud filter keeps the stance aligned with the
    prevailing trend; the base class enters/exits on these state transitions.
    """

    name = "Ichimoku"

    tenkan = 9
    kijun = 26
    senkou = 52
    displacement = 26

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        (
            self.tenkan_sen,
            self.kijun_sen,
            self.senkou_a,
            self.senkou_b,
            self.chikou_span,
        ) = self.I(
            indicators.ichimoku,
            high,
            low,
            close,
            self.tenkan,
            self.kijun,
            self.senkou,
            self.displacement,
        )

    def _above_cloud(self) -> bool:
        price = self.data.Close[-1]
        return price > self.senkou_a[-1] and price > self.senkou_b[-1]

    def _below_cloud(self) -> bool:
        price = self.data.Close[-1]
        return price < self.senkou_a[-1] and price < self.senkou_b[-1]

    def longSignal(self) -> bool:
        return self.tenkan_sen[-1] > self.kijun_sen[-1] and self._above_cloud()

    def shortSignal(self) -> bool:
        return self.tenkan_sen[-1] < self.kijun_sen[-1] and self._below_cloud()
