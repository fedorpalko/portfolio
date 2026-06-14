"""Market data loading via yfinance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

_OHLCV = ["Open", "High", "Low", "Close", "Volume"]


class DataError(Exception):
    """Raised when market data cannot be loaded or is unusable."""


def fetch(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV data for ``ticker`` between ``start`` and ``end``.

    Returns a DataFrame indexed by date with the columns
    ``Open, High, Low, Close, Volume`` (the shape ``backtesting.py`` expects).
    """
    ticker = (ticker or "").strip().upper()
    if not ticker:
        raise DataError("Ticker is empty.")

    try:
        df = yf.download(
            ticker, start=start, end=end, auto_adjust=True, progress=False
        )
    except Exception as exc:  # network / parsing errors
        raise DataError(f"Failed to download {ticker}: {exc}") from exc

    if df is None or df.empty:
        raise DataError(
            f"No data for {ticker} between {start} and {end}. "
            "Check the ticker symbol and date range."
        )

    # Recent yfinance returns MultiIndex columns even for a single ticker.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns=str.title)
    missing = [c for c in _OHLCV if c not in df.columns]
    if missing:
        raise DataError(f"Downloaded data is missing columns: {missing}")

    df = df[_OHLCV].dropna()
    if df.empty:
        raise DataError(f"No usable rows for {ticker} after cleaning.")
    return df
