"""Market data loading via yfinance."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import yfinance as yf

_OHLCV = ["Open", "High", "Low", "Close", "Volume"]

#: Intervals yfinance accepts, coarsest-to-use last.
VALID_INTERVALS = [
    "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h",
    "1d", "5d", "1wk", "1mo", "3mo",
]

# How far back (days from today) yfinance serves each intraday interval.
# Anything not listed (1d and coarser) has effectively unlimited history.
_MAX_LOOKBACK_DAYS = {
    "1m": 30, "2m": 60, "5m": 60, "15m": 60, "30m": 60, "90m": 60,
    "60m": 730, "1h": 730,
}
# Max span yfinance allows per request. Only 1m is tightly capped.
_MAX_SPAN_DAYS = {"1m": 7}


class DataError(Exception):
    """Raised when market data cannot be loaded or is unusable."""


def _parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def check_interval(start: str, end: str, interval: str) -> str | None:
    """Validate an interval against a date range using yfinance's limits.

    Returns a human-readable warning if the combination would fail or return
    no data, or ``None`` if it looks fine. Best-effort: if the dates can't be
    parsed, returns ``None`` and lets :func:`fetch` surface any real error.
    """
    if interval not in VALID_INTERVALS:
        return f"'{interval}' is not a valid yfinance interval."
    try:
        start_d = _parse_date(start)
        end_d = _parse_date(end)
    except (ValueError, TypeError, AttributeError):
        return None

    today = date.today()
    lookback = _MAX_LOOKBACK_DAYS.get(interval)
    if lookback is not None and (today - start_d).days > lookback:
        return (
            f"yfinance only serves {interval} data for roughly the last "
            f"{lookback} days. Your start date ({start}) is too far back, so "
            f"this would return no data. Use a coarser interval (e.g. 1d) or a "
            f"more recent start date."
        )

    span = _MAX_SPAN_DAYS.get(interval)
    if span is not None and (end_d - start_d).days > span:
        return (
            f"yfinance limits {interval} requests to {span} days per call, but "
            f"your range spans {(end_d - start_d).days} days — this will throw "
            f"an error. Shorten the range or pick a coarser interval."
        )
    return None


def fetch(ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV data for ``ticker`` between ``start`` and ``end``.

    ``interval`` is a yfinance bar size (e.g. ``1d``, ``1h``, ``5m``). Returns a
    DataFrame indexed by date with the columns ``Open, High, Low, Close,
    Volume`` (the shape ``backtesting.py`` expects).
    """
    ticker = (ticker or "").strip().upper()
    if not ticker:
        raise DataError("Ticker is empty.")

    try:
        df = yf.download(
            ticker, start=start, end=end, interval=interval,
            auto_adjust=True, progress=False,
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
