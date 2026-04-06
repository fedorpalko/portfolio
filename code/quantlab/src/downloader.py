# downloader.py
from typing import Tuple, Dict, Optional
import pandas as pd
import yfinance as yf


def download_data(ticker: str = "AAPL", start_date: str = "2020-01-01", end_date: str = "2023-01-01", period: str="1h") -> pd.DataFrame:
    """Download OHLCV and return a DataFrame with clean, lowercase column names."""
    df = yf.download(ticker, start=start_date, end=end_date, interval=period, auto_adjust=True)
    if df.empty:
        raise RuntimeError("Downloaded data is empty — check network or ticker/date range")

    # Compact, generic column flattening (works for MultiIndex and single-level)
    new_cols = []
    ticker_suffix = f'_{ticker.lower()}'
    for col in df.columns:
        # Create a string from single or multi-level column names
        if isinstance(col, tuple):
            name = "_".join(str(c).strip() for c in col if c)
        else:
            name = str(col)
        
        # Standardize to lowercase with underscores
        clean_name = name.lower().replace(' ', '_')

        # Remove ticker suffix if yfinance adds it (e.g., 'close_aapl' -> 'close')
        if clean_name.endswith(ticker_suffix):
            clean_name = clean_name[:-len(ticker_suffix)]
        
        new_cols.append(clean_name)
    df.columns = new_cols

    # Ensure required columns for strategies are present
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise KeyError(
            f"Downloaded data is missing one or more required columns "
            f"({', '.join(required_cols)}). Available columns: {df.columns.tolist()}"
        )
    
    # With auto_adjust=True, 'close' is the adjusted close price.
    # The original logic for finding 'adj_close' is no longer necessary.
    return df
