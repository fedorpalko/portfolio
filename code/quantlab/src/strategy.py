# define your signals and conditions here
import pandas as pd
import pandas_ta as ta

# Default parameter ranges for optimization
DEFAULT_PARAM_RANGES = {
    'ema_length': range(50, 101, 10),
    'rsi_length': range(12, 19, 2),
    'adx_length': range(12, 19, 2)
}

def adx_rsi_ema_strategy(df: pd.DataFrame, ema_length: int, rsi_length: int, adx_length: int) -> pd.DataFrame:
    """
    Generates trading signals based on ADX, RSI, and a single EMA.

    Args:
        df (pd.DataFrame): The input DataFrame with 'high', 'low', 'close' columns.
        ema_length (int): The period for the Exponential Moving Average.
        rsi_length (int): The period for the Relative Strength Index.
        adx_length (int): The period for the Average Directional Index.
    """
    adx_threshold = 25
    rsi_midline = 50

    # Calculate indicators
    df[f'EMA_{ema_length}'] = ta.ema(df['close'], length=ema_length)
    df[f'RSI_{rsi_length}'] = ta.rsi(df['close'], length=rsi_length)
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=adx_length)
    # Ensure ADX column exists before using it
    if adx_df is not None and f'ADX_{adx_length}' in adx_df.columns:
        df[f'ADX_{adx_length}'] = adx_df[f'ADX_{adx_length}']
    else:
        df[f'ADX_{adx_length}'] = 0  # Default to 0 if ADX can't be calculated

    # Define conditions for buy and sell signals
    buy_condition = (
        (df['close'] > df[f'EMA_{ema_length}']) &
        (df[f'ADX_{adx_length}'] > adx_threshold) &
        (df[f'RSI_{rsi_length}'] > rsi_midline)
    )
    
    sell_condition = (
        (df['close'] < df[f'EMA_{ema_length}']) &
        (df[f'ADX_{adx_length}'] > adx_threshold) &
        (df[f'RSI_{rsi_length}'] < rsi_midline)
    )
    
    # Generate signals
    df['signal'] = 0
    df.loc[buy_condition, 'signal'] = 1
    df.loc[sell_condition, 'signal'] = -1
    
    return df

def generate_signals(df, params=None):
    """
    Args:
        df (pd.DataFrame): The input DataFrame with a 'close' column.
        params (dict): Parameters for the strategy.
    """
    if params is None:
        params = {'ema_length': 50, 'rsi_length': 14, 'adx_length': 14}
    
    ema_length = params.get('ema_length', 50)
    rsi_length = params.get('rsi_length', 14)
    adx_length = params.get('adx_length', 14)
    
    df = adx_rsi_ema_strategy(df, ema_length=ema_length, rsi_length=rsi_length, adx_length=adx_length)
    # The 'signal' column is now directly created by adx_rsi_ema_strategy
    return df