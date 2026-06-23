"""Indicator helpers.

Prefers ``pandas-ta`` (per the design doc) but transparently falls back to
plain pandas implementations when it is unavailable or fails to import — some
``pandas-ta`` builds break on newer numpy. Either way the strategies get the
same numbers, so the app never hard-depends on the indicator library importing
cleanly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import pandas_ta as _ta  # type: ignore

    _HAVE_TA = True
except Exception:  # pragma: no cover - depends on the environment
    _ta = None
    _HAVE_TA = False


def _series(values) -> pd.Series:
    return pd.Series(np.asarray(values, dtype=float))


def sma(values, period: int):
    close = _series(values)
    if _HAVE_TA:
        out = _ta.sma(close, length=int(period))
        if out is not None:
            return out.to_numpy()
    return close.rolling(int(period)).mean().to_numpy()


def ema(values, period: int):
    close = _series(values)
    if _HAVE_TA:
        out = _ta.ema(close, length=int(period))
        if out is not None:
            return out.to_numpy()
    return close.ewm(span=int(period), adjust=False).mean().to_numpy()


def ma(values, period: int, ma_type: str = "SMA"):
    """Dispatch to SMA or EMA based on ``ma_type`` ("SMA" or "EMA")."""
    if str(ma_type).upper() == "EMA":
        return ema(values, period)
    return sma(values, period)


def macd(values, fast: int = 12, slow: int = 26, signal: int = 9):
    """Return ``(macd_line, signal_line)`` as numpy arrays."""
    close = _series(values)
    if _HAVE_TA:
        df = _ta.macd(close, fast=int(fast), slow=int(slow), signal=int(signal))
        if df is not None and df.shape[1] >= 3:
            return df.iloc[:, 0].to_numpy(), df.iloc[:, 2].to_numpy()
    fast_ema = close.ewm(span=int(fast), adjust=False).mean()
    slow_ema = close.ewm(span=int(slow), adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=int(signal), adjust=False).mean()
    return macd_line.to_numpy(), signal_line.to_numpy()


def ichimoku(
    high,
    low,
    close,
    tenkan: int = 9,
    kijun: int = 26,
    senkou: int = 52,
    displacement: int = 26,
):
    """Ichimoku Kinko Hyo lines as numpy arrays.

    Returns ``(tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span)``.

    The Senkou spans are shifted *forward* by ``displacement`` so that, at any
    index, they hold the cloud value projected onto that bar — i.e. directly
    comparable with the current price (no lookahead). The Chikou span is the
    close shifted *back* by ``displacement`` and is for visualisation only; it
    references future bars and must not be used in live signals.
    """
    high_s = _series(high)
    low_s = _series(low)
    close_s = _series(close)

    def _midpoint(period: int) -> pd.Series:
        rolling_high = high_s.rolling(int(period)).max()
        rolling_low = low_s.rolling(int(period)).min()
        return (rolling_high + rolling_low) / 2

    tenkan_sen = _midpoint(tenkan)
    kijun_sen = _midpoint(kijun)
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(int(displacement))
    senkou_b = _midpoint(senkou).shift(int(displacement))
    chikou_span = close_s.shift(-int(displacement))

    return (
        tenkan_sen.to_numpy(),
        kijun_sen.to_numpy(),
        senkou_a.to_numpy(),
        senkou_b.to_numpy(),
        chikou_span.to_numpy(),
    )


def rsi(values, period: int = 14):
    """Relative Strength Index as a numpy array."""
    close = _series(values)
    if _HAVE_TA:
        out = _ta.rsi(close, length=int(period))
        if out is not None:
            return out.to_numpy()
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = roll_up / roll_down
    return (100 - 100 / (1 + rs)).to_numpy()


def tema(values, period: int = 20):
    """Triple Exponential Moving Average as a numpy array.

    ``TEMA = 3*EMA1 - 3*EMA2 + EMA3`` where each EMA is taken of the previous
    one. Hugs price more tightly than a plain EMA with less lag.
    """
    close = _series(values)
    if _HAVE_TA:
        out = _ta.tema(close, length=int(period))
        if out is not None:
            return out.to_numpy()
    ema1 = close.ewm(span=int(period), adjust=False).mean()
    ema2 = ema1.ewm(span=int(period), adjust=False).mean()
    ema3 = ema2.ewm(span=int(period), adjust=False).mean()
    return (3 * ema1 - 3 * ema2 + ema3).to_numpy()


def adx(high, low, close, period: int = 14):
    """Average Directional Index (Wilder) as a numpy array.

    Measures trend *strength* regardless of direction; values above ~25 are
    commonly read as a trending market.
    """
    high_s = _series(high)
    low_s = _series(low)
    close_s = _series(close)
    if _HAVE_TA:
        df = _ta.adx(high_s, low_s, close_s, length=int(period))
        if df is not None and df.shape[1] >= 1:
            return df.iloc[:, 0].to_numpy()

    up_move = high_s.diff()
    down_move = -low_s.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=high_s.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=high_s.index,
    )
    prev_close = close_s.shift()
    true_range = pd.concat(
        [high_s - low_s, (high_s - prev_close).abs(), (low_s - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    alpha = 1 / int(period)
    atr = true_range.ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=alpha, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False).mean() / atr
    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    return dx.ewm(alpha=alpha, adjust=False).mean().to_numpy()


def cmo(values, period: int = 14):
    """Chande Momentum Oscillator as a numpy array.

    Bounded in ``[-100, 100]``; positive readings mean gains dominate the
    lookback window, negative readings mean losses dominate.
    """
    close = _series(values)
    if _HAVE_TA:
        out = _ta.cmo(close, length=int(period))
        if out is not None:
            return out.to_numpy()
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    sum_up = up.rolling(int(period)).sum()
    sum_down = down.rolling(int(period)).sum()
    denom = (sum_up + sum_down).replace(0, np.nan)
    return (100 * (sum_up - sum_down) / denom).to_numpy()
