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
