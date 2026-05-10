from datetime import datetime
from functools import reduce
from typing import Optional, Union

import numpy as np
import pandas as pd
import talib.abstract as ta
from freqtrade.persistence import Trade
from freqtrade.strategy import (
    CategoricalParameter,
    IStrategy,
    merge_informative_pair,
    stoploss_from_absolute,
)
from pandas import DataFrame


class Gamma(IStrategy):
    """
    Gamma (γ) Strategy - Adjusted Version
    Relaxed entry filters for trade generation while maintaining exit discipline.
    Follows Gamma.md design thesis with softened ADX gates and wider CMO band.
    """

    INTERFACE_VERSION = 3

    minimal_roi = {"0": 100}
    stoploss = -0.99
    trailing_stop = False
    use_custom_stoploss = True
    timeframe = "4h"
    informative_timeframe = "1d"
    can_short = False

    # Startup candle count: TEMA 200 needs 200 candles on 1d, TEMA 50 needs 50 on 4h
    startup_candle_count = 200

    reward_risk_ratio = CategoricalParameter(
        [1.5, 2.0, 2.5, 3.0], default=2.0, space="buy"
    )

    # CMO band for zero-cross filtering - widened for more entries
    # Design: ±10, now: ±15 for more trade signal opportunities
    cmo_band = CategoricalParameter(
        [5, 10, 15, 20], default=15, space="buy"
    )

    # ADX thresholds - relaxed from design to allow more entries
    # 1D gate: design says 25, relaxed to 20
    # 4H confirmation: design says 20, relaxed to 15
    adx_1d_gate = CategoricalParameter(
        [15, 20, 25], default=20, space="buy"
    )
    
    adx_4h_gate = CategoricalParameter(
        [10, 15, 20], default=15, space="buy"
    )

    @property
    def plot_config(self):
        return {
            "main_plot": {
                "tema_21": {"color": "blue"},
                "tema_50": {"color": "orange"},
                "tema_200_1d": {"color": "red"},
            },
            "subplots": {
                "ADX": {"adx": {"color": "blue"}, "adx_1d": {"color": "red"}},
                "CMO": {"cmo": {"color": "green"}},
            },
        }

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe) for pair in pairs]

    def populate_informative_trend(
        self, dataframe: DataFrame, metadata: dict
    ) -> DataFrame:
        dataframe["tema_200"] = ta.TEMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if not self.dp:
            return dataframe

        informative = self.dp.get_pair_dataframe(
            pair=metadata["pair"], timeframe=self.informative_timeframe
        )
        informative = self.populate_informative_trend(informative, metadata)

        dataframe = merge_informative_pair(
            dataframe,
            informative,
            self.timeframe,
            self.informative_timeframe,
            ffill=True,
        )

        dataframe["tema_21"] = ta.TEMA(dataframe, timeperiod=21)
        dataframe["tema_50"] = ta.TEMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["cmo"] = ta.CMO(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Native Crossover Logic
        # TEMA 21 crosses above TEMA 50
        tema_cross_up = (dataframe["tema_21"] > dataframe["tema_50"]) & (
            dataframe["tema_21"].shift(1) <= dataframe["tema_50"].shift(1)
        )

        # CMO crosses above lower band (for long) 
        cmo_band_value = self.cmo_band.value
        cmo_cross_up = (dataframe["cmo"] > cmo_band_value) & (
            dataframe["cmo"].shift(1) <= cmo_band_value
        )

        # Get ADX thresholds from hyperparameters
        adx_1d_threshold = self.adx_1d_gate.value
        adx_4h_threshold = self.adx_4h_gate.value

        # Long entry conditions (all must be true)
        long_conditions = [
            (dataframe["close"] > dataframe["tema_200_1d"]),  # Price above 1D TEMA 200
            (dataframe["adx_1d"] > adx_1d_threshold),          # 1D trend strength gate
            tema_cross_up,                                     # 4H momentum signal
            (dataframe["adx"] > adx_4h_threshold),             # 4H trend confirmation
            cmo_cross_up,                                      # 4H momentum confirmation
        ]

        if long_conditions:
            dataframe.loc[reduce(lambda x, y: x & y, long_conditions), "enter_long"] = 1

        # TEMA 21 crosses below TEMA 50
        tema_cross_down = (dataframe["tema_21"] < dataframe["tema_50"]) & (
            dataframe["tema_21"].shift(1) >= dataframe["tema_50"].shift(1)
        )

        # CMO crosses below negative band
        cmo_cross_down = (dataframe["cmo"] < -cmo_band_value) & (
            dataframe["cmo"].shift(1) >= -cmo_band_value
        )

        # Short entry conditions (all must be true)
        short_conditions = [
            (dataframe["close"] < dataframe["tema_200_1d"]),   # Price below 1D TEMA 200
            (dataframe["adx_1d"] > adx_1d_threshold),          # 1D trend strength gate
            tema_cross_down,                                   # 4H momentum signal
            (dataframe["adx"] > adx_4h_threshold),             # 4H trend confirmation
            cmo_cross_down,                                    # 4H momentum confirmation
        ]

        if short_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, short_conditions), "enter_short"
            ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[:, "exit_short"] = 0
        return dataframe

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        historical_candles = dataframe.loc[dataframe["date"] < trade.open_date]
        if historical_candles.empty:
            return -1.0

        signal_candle = historical_candles.iloc[-1].squeeze()
        atr = signal_candle["atr"]
        sl_distance = 1.5 * atr

        if trade.is_short:
            sl_price = signal_candle["high"] + sl_distance
        else:
            sl_price = signal_candle["low"] - sl_distance

        return stoploss_from_absolute(sl_price, current_rate, is_short=trade.is_short)

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0:
            return None

        current_candle = dataframe.iloc[-1].squeeze()

        # Hard invalidation: 1D ADX drops below gate threshold mid-trade
        adx_1d_threshold = self.adx_1d_gate.value
        if current_candle["adx_1d"] < adx_1d_threshold:
            return "hard_invalidation"

        historical_candles = dataframe.loc[dataframe["date"] < trade.open_date]
        if historical_candles.empty:
            return None

        signal_candle = historical_candles.iloc[-1].squeeze()
        atr = signal_candle["atr"]
        sl_distance = 1.5 * atr
        r_ratio = self.reward_risk_ratio.value

        if trade.is_short:
            sl_price = signal_candle["high"] + sl_distance
            actual_risk_distance = sl_price - trade.open_rate
            tp_price = trade.open_rate - (actual_risk_distance * r_ratio)
            if current_rate <= tp_price:
                return "take_profit"
        else:
            sl_price = signal_candle["low"] - sl_distance
            actual_risk_distance = trade.open_rate - sl_price
            tp_price = trade.open_rate + (actual_risk_distance * r_ratio)
            if current_rate >= tp_price:
                return "take_profit"

        return None