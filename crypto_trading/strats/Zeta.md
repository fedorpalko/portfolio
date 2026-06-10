## Thesis

**Zeta ($\zeta$)** is yet another trading strategy based on the [Universal Growth Rate Model](../papers/EV_paper.md). This strategy is a mean-reversion strategy designed for medium-high market cap coins (think the top 20-30 coins, excluding the top 3 and stablecoins) that applies the universal model, but it doesn't base the entire strategy on it. Instead it utilizes it as a simple validator of whether it is viable, and it employs different models to generate a profit that is more substantial than Gamma, while compensating for that by requiring higher risk. It is no longer a strategy for retail traders that can use high capital to generate returns with small % of profits.

## Table of Contents

1. Core strategy definition, parameter choosing
2. Strategy implementation (theoretical)
3. Strategy backtesting, analysis
4. Strategy validation via $G$
5. Conclusion

## 1. Core strategy definition, parameter choosing

> For this strategy, we choose to trade on **Binance Futures**, non-US.

### 1.1 Parameters

| Parameter | Value | Rationale |
|:-----------|:-------|:---------|
| $C$ | 10 000 | Capital defined as the avg. portfolio value for hobby traders |
| $S$ | 0.05 | Position sizing that is riskier|
| $f_e$ | 0.0005 | Binance taker entry fee |
| $f_x$ | 0.0005 | Binance taker exit fee |
| $L$ | 3 | Leverage of 3x to increase the potential returns |
| $\bar{R}$ | 2 | Reward target is set to 2x the risk |

### 1.2 Pairs

Below is a list of chosen pairs to trade:
- `LINK/USDT:USDT`
- `ADA/USDT:USDT`
- `POL/USDT:USDT`
- `DOT/USDT:USDT`
- `AVAX/USDT:USDT`

### 1.3 Timeframes

| Role | Timeframe |
|:-----------|:-----------|
| Informative | 1H |
| Execution | 15m |

## 2. Strategy implementation (theoretical)

### 2.1 Core idea

Zeta will be a mean-reversion strategy, utilizing quick changes in volatility and direction and short trade durations to make a profit. For entry, it'll have clear rigid rules, while for exit there are three options: taking profit, stoploss, and an exit trend detector. The goal is to create a strategy with:

### 2.2 Indicators

| Indicator | Role | Initial Value |
| :-------------------------: | :-----------: | :-----------: | 
| RSI | Overbought/oversold | 14 for period, 35/65 for oversold/overbought |
| Bollinger Bands | Volatility, price action | 20 for period, 2 std devs |
| ATR | Stop loss placement | 1.5x below price, take profit at 2x ATR above price |

### 2.3 Entry Conditions

**Long:**
- RSI $ \le $ 35
- Price closes below the lower Bollinger Band
- 15m candle closes below the lower Bollinger Band

**Short:**
- RSI $ \ge $ 65
- Price closes above the upper Bollinger Band
- 15m candle closes above the upper Bollinger Band

### 2.4 Exit Conditions

**Take Profit:**
- Price reaches 2x ATR above the entry price

**Stop Loss:**
- Price reaches 1.5x ATR below the entry price
 
**Exit Trend:**
- Price closes below the lower Bollinger Band (long only)
- Price closes above the upper Bollinger Band (short only)

## 3. Strategy backtesting, analysis

For this section, we performed multiple backtests on **Binance Futures** in the following periods:

| Date Range | Condition | PnL (%) | Sharpe | Sortino | Max Drawdown (%) | $\bar{\omega}$
|-----------|-----------|--------|---------|------------------|----------------|----------|
| `20260101-20260301` | Choppy | 

## 4. Strategy validation via $G$

> To be done

## 5. Conclusion

> To be done
