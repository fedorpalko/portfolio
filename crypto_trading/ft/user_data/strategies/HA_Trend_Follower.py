# HA_Trend_Follower.py
# S001 — Phase IV implementation
#
# Signal layer  : Heikin-Ashi candles (4H) — EMA 21, ADX(14)
# Regime layer  : Real candles (1D)        — EMA 50, EMA 200
# Execution layer: Real candles (4H)       — RSI(14), ATR(14), fills, stops, targets
#
# Position sizing: dynamic half-Kelly via custom_stake_amount()
# Orders        : limit only (f_r = 0.0004 assumption)
# Leverage      : 2x
# Pairs         : BTC, ETH, SOL, BNB, LINK — USDT perpetuals on Bitget

import numpy as np
import pandas as pd
from datetime import datetime
from freqtrade.strategy import IStrategy

from freqtrade.persistence import Trade
from typing import Optional
import talib.abstract as ta


class HA_Trend_Follower(IStrategy):

    # -------------------------------------------------------------------------
    # Strategy metadata
    # -------------------------------------------------------------------------
    INTERFACE_VERSION = 3
    timeframe = "4h"
    inf_timeframe = "1d"

    # startup_candle_count tells Freqtrade how much extra historical data to
    # load before the backtest window starts, so indicators are valid from
    # candle 1. EMA 200 on 1D needs 200 daily candles = 1200 4H candles.
    # ATR 50-period average on 4H adds ~50 more. Round up to 1250.
    startup_candle_count: int = 1250

    # -------------------------------------------------------------------------
    # S001 hard constraints (Phase II §2.5)
    # -------------------------------------------------------------------------
    leverage_value: float = 2.0
    fee_rate: float = 0.0004          # Bitget limit order round-trip
    r2: float = 1.0                   # risk ratio (symmetric stops)
    atr_multiplier_sl: float = 2.5    # stop  = 1x ATR
    atr_multiplier_tp: float = 3.0    # target = 2x ATR  ->  r = 2.0 baseline
    atr_regime_cap: float = 1.2       # skip if ATR > 1.5x its 50-period avg
    adx_threshold: float = 25.0       # trend strength gate
    rsi_long_low: float = 40.0
    rsi_long_high: float = 70.0
    rsi_short_low: float = 30.0
    rsi_short_high: float = 60.0

    # -------------------------------------------------------------------------
    # Kelly / position sizing
    # -------------------------------------------------------------------------
    kelly_lookback: int = 30          # rolling window of closed trades
    kelly_fallback: float = 0.10      # conservative fraction when < 30 trades
    kelly_fraction: float = 0.5       # half-Kelly

    # -------------------------------------------------------------------------
    # ATR snapshot at entry — locks stop and target to entry-candle volatility.
    # Keyed by pair string. Prevents custom_stoploss from drifting as ATR
    # changes during the trade, which Freqtrade misreads as trailing.
    # -------------------------------------------------------------------------
    trade_entry_atr: dict = {}

    # -------------------------------------------------------------------------
    # Freqtrade position/trade config
    # -------------------------------------------------------------------------
    max_open_trades: int = 1
    can_short: bool = True

    # Stoploss managed dynamically via custom_stoploss.
    # This wide value is a hard safety net only.
    stoploss: float = -0.99
    use_custom_stoploss: bool = True

    # ROI disabled — exits handled entirely by custom_exit (ATR TP)
    minimal_roi = {"0": 100}

    trailing_stop: bool = False

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "limit",
        "stoploss_on_exchange": True,
    }

    # -------------------------------------------------------------------------
    # Informative pairs (1D real candles for regime filter)
    # -------------------------------------------------------------------------
    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.inf_timeframe) for pair in pairs]

    # -------------------------------------------------------------------------
    # Heikin-Ashi candle computation
    # -------------------------------------------------------------------------
    @staticmethod
    def _compute_ha(dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Computes Heikin-Ashi OHLC from real candles.
        HA prices are synthetic — signal generation only, never execution.
        """
        ha = dataframe.copy()
        ha["ha_close"] = (
            dataframe["open"] + dataframe["high"] +
            dataframe["low"] + dataframe["close"]
        ) / 4.0

        ha_open = [(dataframe["open"].iloc[0] + dataframe["close"].iloc[0]) / 2.0]
        for i in range(1, len(dataframe)):
            ha_open.append((ha_open[i - 1] + ha["ha_close"].iloc[i - 1]) / 2.0)
        ha["ha_open"] = ha_open

        ha["ha_high"] = pd.concat(
            [ha["ha_open"], ha["ha_close"], dataframe["high"]], axis=1
        ).max(axis=1)
        ha["ha_low"] = pd.concat(
            [ha["ha_open"], ha["ha_close"], dataframe["low"]], axis=1
        ).min(axis=1)

        return ha

    # -------------------------------------------------------------------------
    # Indicators
    # -------------------------------------------------------------------------
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        # --- 1D real candle regime indicators --------------------------------
        inf_df = self.dp.get_pair_dataframe(
            pair=metadata["pair"], timeframe=self.inf_timeframe
        )
        inf_df["ema50_1d"] = ta.EMA(inf_df["close"], timeperiod=50)
        inf_df["ema200_1d"] = ta.EMA(inf_df["close"], timeperiod=200)

        # merge_asof aligns each 4H row to the most recent prior 1D candle.
        # This is the correct way to bring higher-TF data into a lower-TF
        # dataframe — merge() on exact timestamps leaves NaN on most rows.
        inf_df = inf_df[["date", "ema50_1d", "ema200_1d"]].copy()
        inf_df["date"] = pd.to_datetime(inf_df["date"], utc=True)
        dataframe["date"] = pd.to_datetime(dataframe["date"], utc=True)

        dataframe = pd.merge_asof(
            dataframe.sort_values("date"),
            inf_df.sort_values("date"),
            on="date",
            direction="backward"
        )

        # --- 4H Heikin-Ashi signal indicators --------------------------------
        ha = self._compute_ha(dataframe)

        ha["ha_ema21"] = ta.EMA(ha["ha_close"], timeperiod=21)
        ha["ha_adx"] = ta.ADX(
            ha["ha_high"], ha["ha_low"], ha["ha_close"], timeperiod=14
        )

        # Crossover: HA close was at or below EMA 21 last candle, now above
        ha["ha_crossed_above_ema21"] = (
            (ha["ha_close"] > ha["ha_ema21"]) &
            (ha["ha_close"].shift(1) <= ha["ha_ema21"].shift(1))
        )
        # Crossunder: mirror for shorts
        ha["ha_crossed_below_ema21"] = (
            (ha["ha_close"] < ha["ha_ema21"]) &
            (ha["ha_close"].shift(1) >= ha["ha_ema21"].shift(1))
        )

        # Merge HA signal columns into real-candle dataframe
        dataframe["ha_ema21"] = ha["ha_ema21"].values
        dataframe["ha_adx"] = ha["ha_adx"].values
        dataframe["ha_crossed_above_ema21"] = ha["ha_crossed_above_ema21"].values
        dataframe["ha_crossed_below_ema21"] = ha["ha_crossed_below_ema21"].values

        # --- 4H real candle execution indicators -----------------------------
        dataframe["rsi"] = ta.RSI(dataframe["close"], timeperiod=14)
        dataframe["atr"] = ta.ATR(
            dataframe["high"], dataframe["low"], dataframe["close"], timeperiod=14
        )
        dataframe["atr_avg50"] = dataframe["atr"].rolling(50).mean()
        dataframe["atr_regime_ok"] = (
            dataframe["atr"] < self.atr_regime_cap * dataframe["atr_avg50"]
        )

        return dataframe

    # -------------------------------------------------------------------------
    # Entry signals
    # -------------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        # Explicitly initialise signal columns with correct dtypes before any
        # conditional assignment. Freqtrade's signal reader requires clean
        # integer 1s — pandas multi-column slice assignment with mixed types
        # ([1, "string"]) does not guarantee this.
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe["enter_tag"] = ""

        long_condition = (
            (dataframe["close"] > dataframe["ema200_1d"]) &
            (dataframe["ema50_1d"] > dataframe["ema200_1d"]) &
            (dataframe["ha_adx"] > self.adx_threshold) &
            (dataframe["ha_crossed_above_ema21"]) &
            (dataframe["rsi"] > self.rsi_long_low) &
            (dataframe["rsi"] < self.rsi_long_high) &
            (dataframe["atr_regime_ok"]) &
            (dataframe["volume"] > 0)
        )

        dataframe.loc[long_condition, "enter_long"] = 1
        dataframe.loc[long_condition, "enter_tag"] = "ha_ema21_pullback_long"

        short_condition = (
            (dataframe["close"] < dataframe["ema200_1d"]) &
            (dataframe["ema50_1d"] < dataframe["ema200_1d"]) &
            (dataframe["ha_adx"] > self.adx_threshold) &
            (dataframe["ha_crossed_below_ema21"]) &
            (dataframe["rsi"] > self.rsi_short_low) &
            (dataframe["rsi"] < self.rsi_short_high) &
            (dataframe["atr_regime_ok"]) &
            (dataframe["volume"] > 0)
        )

        dataframe.loc[short_condition, "enter_short"] = 1
        dataframe.loc[short_condition, "enter_tag"] = "ha_ema21_pullback_short"

        return dataframe

    # -------------------------------------------------------------------------
    # Exit signals
    # -------------------------------------------------------------------------
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Exits handled by custom_stoploss and custom_exit
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    # -------------------------------------------------------------------------
    # Confirm trade entry — snapshot ATR at the entry candle.
    # This value is used by custom_stoploss and custom_exit to keep stop and
    # target fixed for the lifetime of the trade.
    # -------------------------------------------------------------------------
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
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if not dataframe.empty:
            self.trade_entry_atr[pair] = dataframe.iloc[-1]["atr"]
        return True

    # -------------------------------------------------------------------------
    # Custom stoploss — ATR-based: entry +/- 1x ATR (locked at entry)
    # -------------------------------------------------------------------------
    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        atr = self.trade_entry_atr.get(pair)
        if atr is None:
            return self.stoploss

        if trade.is_short:
            stop_price = trade.open_rate + (self.atr_multiplier_sl * atr)
            return (stop_price - current_rate) / current_rate
        else:
            stop_price = trade.open_rate - (self.atr_multiplier_sl * atr)
            return (stop_price - current_rate) / current_rate

    # -------------------------------------------------------------------------
    # Custom exit — ATR take-profit: entry +/- 2x ATR (locked at entry)
    # -------------------------------------------------------------------------
    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        atr = self.trade_entry_atr.get(pair)
        if atr is None:
            return None

        if trade.is_short:
            tp_price = trade.open_rate - (self.atr_multiplier_tp * atr)
            if current_rate <= tp_price:
                return "atr_tp_short"
        else:
            tp_price = trade.open_rate + (self.atr_multiplier_tp * atr)
            if current_rate >= tp_price:
                return "atr_tp_long"

        return None

    # -------------------------------------------------------------------------
    # Dynamic half-Kelly position sizing
    # -------------------------------------------------------------------------
    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """
        Backtesting mode: Trade.get_trades() is not supported, so we detect
        the run mode and use the fallback fraction directly.

        Live/dry-run mode: compute half-Kelly from the last 30 closed trades.
        Falls back to kelly_fallback (10%) when history is insufficient.
        """
        available_capital = self.wallets.get_available_stake_amount()

        # Backtesting and hyperopt don't have a live trade database
        if self.config.get("runmode", "").value in ("backtest", "hyperopt"):
            stake = available_capital * self.kelly_fallback
            return max(min_stake or 0, min(stake, max_stake))

        # Live / dry-run: dynamic Kelly from trade history
        try:
            closed_trades = Trade.get_trades(
                [Trade.is_open.is_(False)]
            ).order_by(Trade.close_date.desc()).limit(self.kelly_lookback).all()
        except Exception:
            stake = available_capital * self.kelly_fallback
            return max(min_stake or 0, min(stake, max_stake))

        if len(closed_trades) < self.kelly_lookback:
            stake = available_capital * self.kelly_fallback
            return max(min_stake or 0, min(stake, max_stake))

        wins = [t for t in closed_trades if t.profit_ratio > 0]
        losses = [t for t in closed_trades if t.profit_ratio <= 0]

        if not wins or not losses:
            stake = available_capital * self.kelly_fallback
            return max(min_stake or 0, min(stake, max_stake))

        w = len(wins) / len(closed_trades)
        avg_win = np.mean([t.profit_ratio for t in wins])
        avg_loss = abs(np.mean([t.profit_ratio for t in losses]))

        if avg_loss == 0:
            stake = available_capital * self.kelly_fallback
            return max(min_stake or 0, min(stake, max_stake))

        r = avg_win / avg_loss
        kelly = (w * r - (1 - w) * self.r2) / r
        half_kelly = self.kelly_fraction * kelly

        # Hard clamp: never risk less than 2% or more than 25%
        half_kelly = max(0.02, min(half_kelly, 0.25))

        stake = available_capital * half_kelly
        return max(min_stake or 0, min(stake, max_stake))

    # -------------------------------------------------------------------------
    # Leverage — fixed at 2x per Phase I spec
    # -------------------------------------------------------------------------
    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        return self.leverage_value
