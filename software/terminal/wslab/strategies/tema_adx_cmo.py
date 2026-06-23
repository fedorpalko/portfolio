"""Custom strategy: TEMA + ADX + CMO trend-momentum.

Drop-in WSLAB strategy combining three signals:

* **TEMA**  - direction: price above/below the triple-EMA trend line.
* **ADX**   - regime filter: only act when the trend is strong enough.
* **CMO**   - momentum confirmation: sign of the Chande Momentum Oscillator.
"""

from wslab.strategy import WSlabStrategy

from engine import indicators


class TemaAdxCmo(WSlabStrategy):
    """TEMA + ADX + CMO trend-momentum.

    Goes long when price is above the TEMA and the CMO is positive, short when
    price is below the TEMA and the CMO is negative — but only while ADX is
    above its threshold, so the strategy stays flat in choppy, trendless
    markets.
    """

    name = "TEMA+ADX+CMO"

    tema_period = 20
    adx_period = 14
    adx_threshold = 25
    cmo_period = 14

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        self.tema = self.I(indicators.tema, close, self.tema_period)
        self.adx = self.I(indicators.adx, high, low, close, self.adx_period)
        self.cmo = self.I(indicators.cmo, close, self.cmo_period)

    def _trending(self) -> bool:
        return self.adx[-1] > self.adx_threshold

    def longSignal(self) -> bool:
        price = self.data.Close[-1]
        return self._trending() and price > self.tema[-1] and self.cmo[-1] > 0

    def shortSignal(self) -> bool:
        price = self.data.Close[-1]
        return self._trending() and price < self.tema[-1] and self.cmo[-1] < 0
