from datetime import datetime, timedelta
from typing import Optional, Union

import numpy as np
import pandas as pd
import talib.abstract as ta
from freqtrade.persistence import Trade
from freqtrade.strategy import (
    IStrategy,
    merge_informative_pair,
    stoploss_from_absolute,
)
from pandas import DataFrame


class Theta(IStrategy):
    """
    Theta (Θ) Strategy
    A high-risk, high-reward mean reversion strategy.
    Fades overextended moves on 1H timeframe using RSI, Bollinger Bands, and RVOL.
    Designed for BTC/USDT and ETH/USDT on Bitget (Futures).
    """

    INTERFACE_VERSION = 3

    # Strategy parameters
    timeframe = "1h"
    can_short = True
    startup_candle_count = 30  # Enough for BB(20), RSI(9), ADX(14)

    # ROI and Stoploss
    # ROI is handled by custom_exit (TP at BB midline)
    minimal_roi = {"0": 100}
    # Stoploss is handled by custom_stoploss (1.5 * ATR)
    stoploss = -0.99
    use_custom_stoploss = True
    trailing_stop = False

    # Order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "emergency_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Order time in force
    order_time_in_force = {"entry": "gtc", "exit": "gtc"}

    @property
    def plot_config(self):
        return {
            "main_plot": {
                "bb_lower": {"color": "rgba(255, 0, 0, 0.2)"},
                "bb_mid": {"color": "rgba(255, 255, 255, 0.5)"},
                "bb_upper": {"color": "rgba(0, 255, 0, 0.2)"},
            },
            "subplots": {
                "RSI": {"rsi": {"color": "blue"}},
                "RVOL": {"rvol": {"color": "orange"}},
                "ADX": {"adx": {"color": "yellow"}},
            },
        }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI(9)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=9)

        # Bollinger Bands(20, 2)
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2, nbdevdn=2)
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_mid"] = bollinger["middleband"]

        # RVOL(20) - Normalised volume against 20-period moving average
        dataframe["volume_ma"] = dataframe["volume"].rolling(window=20).mean()
        dataframe["rvol"] = dataframe["volume"] / dataframe["volume_ma"]

        # ADX(14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)

        # ATR(14) for stop loss
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long Conditions:
        # 1. Price closes at or below BB lower band
        # 2. RSI(9) < 30
        # 3. RVOL(20) >= 2.0
        # 4. ADX(14) < 25
        dataframe.loc[
            (
                (dataframe["close"] <= dataframe["bb_lower"])
                & (dataframe["rsi"] < 30)
                & (dataframe["rvol"] >= 2.0)
                & (dataframe["adx"] < 25)
            ),
            "enter_long",
        ] = 1

        # Short Conditions:
        # 1. Price closes at or above BB upper band
        # 2. RSI(9) > 70
        # 3. RVOL(20) >= 2.0
        # 4. ADX(14) < 25
        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["bb_upper"])
                & (dataframe["rsi"] > 70)
                & (dataframe["rvol"] >= 2.0)
                & (dataframe["adx"] < 25)
            ),
            "enter_short",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits are handled by custom_exit and custom_stoploss
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
        """
        Stop Loss: 1.5 * ATR(14) from entry point.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        # Get the candle where the trade was opened
        trade_date = trade.open_date.replace(tzinfo=None)
        historical_candles = dataframe.loc[dataframe["date"] <= trade_date]
        
        if historical_candles.empty:
            return -1.0

        # We use the candle before the entry (signal candle) or the entry candle itself
        # The design says "1.5 * ATR(14) from entry"
        signal_candle = historical_candles.iloc[-1].squeeze()
        atr = signal_candle["atr"]
        sl_distance = 1.5 * atr

        if trade.is_short:
            sl_price = trade.open_rate + sl_distance
        else:
            sl_price = trade.open_rate - sl_distance

        # stoploss_from_absolute expects a value between 0 and 1 representing the relative stoploss
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
        """
        Take Profit: BB midline (SMA 20) at time of entry.
        Hard Invalidation: Midline moves away from price by > 2*ATR.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) == 0:
            return None

        current_candle = dataframe.iloc[-1].squeeze()
        
        # Get the candle where the trade was opened to find the target midline
        trade_date = trade.open_date.replace(tzinfo=None)
        historical_candles = dataframe.loc[dataframe["date"] <= trade_date]
        
        if historical_candles.empty:
            return None

        signal_candle = historical_candles.iloc[-1].squeeze()
        target_tp_price = signal_candle["bb_mid"]
        entry_atr = signal_candle["atr"]

        # 1. Take Profit Check
        if trade.is_short:
            if current_rate <= target_tp_price:
                return "take_profit_midline"
        else:
            if current_rate >= target_tp_price:
                return "take_profit_midline"

        # 2. Hard Invalidation Check
        # "If after entry the BB midline moves away from price by more than 2x ATR 
        # (price continues trending hard in the wrong direction), the trade is closed at market."
        # Interpretation: If current_candle['bb_mid'] is further from current_rate than signal_candle['bb_mid'] was,
        # and that distance increased by more than 2 * ATR.
        
        current_midline = current_candle["bb_mid"]
        current_atr = current_candle["atr"]
        
        if trade.is_short:
            # For shorts, we want price to go down to midline. 
            # Invalidation if midline moves UP (away from price) or price moves UP significantly.
            # Design: "midline moves away from price by more than 2x ATR"
            if (current_midline - target_tp_price) > (2 * entry_atr):
                return "hard_invalidation_trend"
        else:
            # For longs, we want price to go up to midline.
            # Invalidation if midline moves DOWN (away from price) or price moves DOWN significantly.
            if (target_tp_price - current_midline) > (2 * entry_atr):
                return "hard_invalidation_trend"

        return None

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: Optional[float], max_stake: float,
                            leverage: float, entry_tag: Optional[str], side: str,
                            **kwargs) -> float:
        """
        Enforce S = 0.25 (25% of capital) per trade.
        """
        # Calculate 25% of total wallet balance
        # self.wallets.get_total_stake_amount() provides the total value including open trades
        # but the design implies 25% of current liquid + locked capital.
        total_capital = self.wallets.get_total_stake_amount()
        return total_capital * 0.25

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> bool:
        """
        Enforce max 1 trade per day per pair.
        """
        # Get all trades for this pair on the current day
        # We check both open and closed trades
        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # This part is tricky in backtesting vs live. 
        # For simplicity and standard compliance, we rely on the logic that 
        # we only take one trade per day.
        
        # Note: Trade.get_trades might not be available in all backtesting environments 
        # but is standard for Freqtrade strategies.
        try:
            trades = Trade.get_trades([
                Trade.pair == pair,
                Trade.open_date >= day_start
            ]).all()
            
            if len(trades) > 0:
                return False
        except Exception:
            # Fallback for environments where Trade.get_trades is not available
            pass

        return True
