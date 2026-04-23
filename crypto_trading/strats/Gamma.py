import numpy as np
import pandas as pd
from pandas import DataFrame
from typing import Optional, Union
from datetime import datetime
from functools import reduce

from freqtrade.strategy import (
    IStrategy,
    CategoricalParameter,
    merge_informative_pair,
    stoploss_from_absolute
)
from freqtrade.persistence import Trade

import talib.abstract as ta
import qtpylib

class Gamma(IStrategy):
    """
    Gamma (γ) Strategy
    
    A trend-following strategy designed for portfolio managers, utilizing
    the Universal Growth Rate Model (G) to find minimal values of win rate,
    reward, and volatility for acceptable return rates.
    """
    
    INTERFACE_VERSION = 3

    # We use custom_exit for TP and custom_stoploss for SL
    minimal_roi = {
        "0": 100
    }

    stoploss = -0.99

    trailing_stop = False

    timeframe = '4h'
    informative_timeframe = '1d'

    # The strategy explicitly defines short logic
    can_short = True

    # R (reward/risk ratio) from the thesis
    reward_risk_ratio = CategoricalParameter([1.5, 2.0, 2.5, 3.0], default=2.0, space='buy')

    @property
    def plot_config(self):
        return {
            'main_plot': {
                'tema_21': {'color': 'blue'},
                'tema_50': {'color': 'orange'},
                'tema_200_1d': {'color': 'red'}
            },
            'subplots': {
                "ADX": {
                    'adx': {'color': 'blue'},
                    'adx_1d': {'color': 'red'}
                },
                "CMO": {
                    'cmo': {'color': 'green'}
                }
            }
        }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        """
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe) for pair in pairs]

    def populate_informative_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        1D Trend Filter Indicators
        """
        dataframe['tema_200'] = ta.TEMA(dataframe, timeperiod=200)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
        """
        if not self.dp:
            return dataframe
            
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        informative = self.populate_informative_trend(informative, metadata)
        
        # Merge the informative pairs to the normal dataframe
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)
        
        # 4H Entry Signal Indicators
        dataframe['tema_21'] = ta.TEMA(dataframe, timeperiod=21)
        dataframe['tema_50'] = ta.TEMA(dataframe, timeperiod=50)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['cmo'] = ta.CMO(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        """
        long_conditions = [
            (dataframe['close'] > dataframe['tema_200_1d']),
            (dataframe['adx_1d'] > 25),
            qtpylib.crossed_above(dataframe['tema_21'], dataframe['tema_50']),
            (dataframe['adx'] > 20),
            qtpylib.crossed_above(dataframe['cmo'], 0)
        ]
        
        if long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, long_conditions),
                'enter_long'
            ] = 1

        short_conditions = [
            (dataframe['close'] < dataframe['tema_200_1d']),
            (dataframe['adx_1d'] > 25),
            qtpylib.crossed_below(dataframe['tema_21'], dataframe['tema_50']),
            (dataframe['adx'] > 20),
            qtpylib.crossed_below(dataframe['cmo'], 0)
        ]

        if short_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, short_conditions),
                'enter_short'
            ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe.
        We handle exits dynamically in custom_exit and custom_stoploss.
        """
        dataframe.loc[:, 'exit_long'] = 0
        dataframe.loc[:, 'exit_short'] = 0
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        """
        Custom stoploss callback.
        Calculates ATR (14) x 1.5 from entry, placed below the entry candle low (long) 
        or above the entry candle high (short).
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        
        # Get the signal candle (the one immediately preceding the trade open)
        historical_candles = dataframe.loc[dataframe['date'] < trade.open_date]
        if historical_candles.empty:
            return -1.0
            
        signal_candle = historical_candles.iloc[-1].squeeze()
        atr = signal_candle['atr']
        sl_distance = 1.5 * atr
        
        if trade.is_short:
            sl_price = signal_candle['high'] + sl_distance
        else:
            sl_price = signal_candle['low'] - sl_distance
            
        return stoploss_from_absolute(sl_price, current_rate, is_short=trade.is_short)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs):
        """
        Custom exit callback for dynamic Take Profit and Hard Invalidation.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0:
            return None
            
        current_candle = dataframe.iloc[-1].squeeze()
        
        # Hard invalidation: 1D ADX drops below 25 mid-trade -> close at market
        if current_candle['adx_1d'] < 25:
            return "hard_invalidation"
            
        # Take profit calculation based on R
        historical_candles = dataframe.loc[dataframe['date'] < trade.open_date]
        if historical_candles.empty:
            return None
            
        signal_candle = historical_candles.iloc[-1].squeeze()
        atr = signal_candle['atr']
        sl_distance = 1.5 * atr
        
        r_ratio = self.reward_risk_ratio.value
        
        if trade.is_short:
            sl_price = signal_candle['high'] + sl_distance
            actual_risk_distance = sl_price - trade.open_rate
            tp_price = trade.open_rate - (actual_risk_distance * r_ratio)
            if current_rate <= tp_price:
                return "take_profit"
        else:
            sl_price = signal_candle['low'] - sl_distance
            actual_risk_distance = trade.open_rate - sl_price
            tp_price = trade.open_rate + (actual_risk_distance * r_ratio)
            if current_rate >= tp_price:
                return "take_profit"

        return None
