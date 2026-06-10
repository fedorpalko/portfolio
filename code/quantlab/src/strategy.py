# define your signals and conditions here
import pandas as pd
import pandas_ta as ta

# Default parameter ranges for optimization
DEFAULT_PARAM_RANGES = {
    'ema_length': range(50, 101, 10),
    'rsi_length': range(12, 19, 2),
    'adx_length': range(12, 19, 2)
}

DEFAULT_PARAM_RANGES_GAMMA = {
    'tema_fast': range(15, 30, 5),
    'tema_slow': range(40, 65, 10),
    'adx_length': range(10, 20, 5),
    'cmo_length': range(10, 20, 5),
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

def gamma_strategy(df: pd.DataFrame, tema_fast: int = 21, tema_slow: int = 50, adx_length: int = 14, cmo_length: int = 14) -> pd.DataFrame:
    """
    Single-timeframe adaptation of the Gamma (γ) strategy from crypto_trading/strats/Gamma.md.
    Uses TEMA crossover + ADX trend filter + CMO momentum confirmation.
    """
    adx_threshold = 20
    cmo_band = 15

    df[f'TEMA_{tema_fast}'] = ta.tema(df['close'], length=tema_fast)
    df[f'TEMA_{tema_slow}'] = ta.tema(df['close'], length=tema_slow)

    adx_df = ta.adx(df['high'], df['low'], df['close'], length=adx_length)
    if adx_df is not None and f'ADX_{adx_length}' in adx_df.columns:
        df[f'ADX_{adx_length}'] = adx_df[f'ADX_{adx_length}']
    else:
        df[f'ADX_{adx_length}'] = 0

    df[f'CMO_{cmo_length}'] = ta.cmo(df['close'], length=cmo_length)

    tema_cross_up = (
        (df[f'TEMA_{tema_fast}'] > df[f'TEMA_{tema_slow}']) &
        (df[f'TEMA_{tema_fast}'].shift(1) <= df[f'TEMA_{tema_slow}'].shift(1))
    )
    tema_cross_down = (
        (df[f'TEMA_{tema_fast}'] < df[f'TEMA_{tema_slow}']) &
        (df[f'TEMA_{tema_fast}'].shift(1) >= df[f'TEMA_{tema_slow}'].shift(1))
    )

    cmo_cross_up = (
        (df[f'CMO_{cmo_length}'] > cmo_band) &
        (df[f'CMO_{cmo_length}'].shift(1) <= cmo_band)
    )
    cmo_cross_down = (
        (df[f'CMO_{cmo_length}'] < -cmo_band) &
        (df[f'CMO_{cmo_length}'].shift(1) >= -cmo_band)
    )

    buy_condition = tema_cross_up & (df[f'ADX_{adx_length}'] > adx_threshold) & cmo_cross_up
    sell_condition = tema_cross_down & (df[f'ADX_{adx_length}'] > adx_threshold) & cmo_cross_down

    df['signal'] = 0
    df.loc[buy_condition, 'signal'] = 1
    df.loc[sell_condition, 'signal'] = -1

    return df


STRATEGY_MAP = {
    'adx_rsi_ema': adx_rsi_ema_strategy,
    'gamma': gamma_strategy,
}


def get_param_ranges(strategy_name: str) -> dict:
    if strategy_name == 'gamma':
        return DEFAULT_PARAM_RANGES_GAMMA
    return DEFAULT_PARAM_RANGES


def generate_signals(df, params=None, strategy_name='adx_rsi_ema'):
    """
    Args:
        df (pd.DataFrame): The input DataFrame with a 'close' column.
        params (dict): Parameters for the strategy.
        strategy_name (str): Which strategy to run ('adx_rsi_ema' or 'gamma').
    """
    if strategy_name == 'gamma':
        if params is None:
            params = {'tema_fast': 21, 'tema_slow': 50, 'adx_length': 14, 'cmo_length': 14}
        df = gamma_strategy(
            df,
            tema_fast=params.get('tema_fast', 21),
            tema_slow=params.get('tema_slow', 50),
            adx_length=params.get('adx_length', 14),
            cmo_length=params.get('cmo_length', 14),
        )
    else:
        if params is None:
            params = {'ema_length': 50, 'rsi_length': 14, 'adx_length': 14}
        df = adx_rsi_ema_strategy(
            df,
            ema_length=params.get('ema_length', 50),
            rsi_length=params.get('rsi_length', 14),
            adx_length=params.get('adx_length', 14),
        )
    return df