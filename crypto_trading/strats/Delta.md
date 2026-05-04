## Thesis

**Delta ($\delta$)** is a trading strategy grounded and built upon the rigorous [Universal Growth Rate Model](../EV_paper.md). The strategy is designed for institutions who seek to achieve higher returns than Gamma, while accepting a higher potential risk or volatility.
 
It also utilizes integration and $G$ to find minimal values of win rate, reward and volatility for an acceptable return rate and growth factor and therefore determine whether the strategy is mathematically viable.

## Development Plan

1. Defining strategy scope
2. Deploying $G$ and locating the thresholds for $\bar{\omega}$, $\bar{R}$ and $\sigma$
3. Designing the strategy
4. Implementing the strategy
5. Backtesting the strategy
6. Validating the strategy
7. Conclusion

## 1. Defining Strategy Scope

Delta's main goal is to generate profit by following trends in the market. It also aims to utilize clear downtrends and uptrends, just like Gamma. The difference here is the acceptance of a higher $\sigma$, using a higher $\bar{R}$ and aiming to achieve an overall higher $G$, where we don't rely on $\bar{\omega}$ as much as Gamma does. 

- Position sizing is determined via $S = 0.05$ to achieve potentially higher $G$ while accepting higher risk
- Capital is defined as $C = 1,000,000\$$
- Fees are defined as $f_e = f_x = 0$ due to Kraken's zero maker fee policy on limit orders for high volume traders (who we are)
- Leverage is set at $L=2$
- We are trading futures pairs using limit orders on Kraken

## 2. Deploying $G$ and Locating the Thresholds

The goal of this phase is to determine the minimum parameter constraints that any algorithm implementing Delta must satisfy to guarantee $\mathbb{E}[G] \geq G_{\text{goal}} = 0.05$.

Since $\bar{\omega}$ is unknown prior to backtesting and not uniformly distributed — a 55% win rate is far more plausible than a 90% win rate for a high-risk trend-following strategy on futures — we model it using a **Beta distribution**, defined on $(0, 1)$ and flexible enough to encode realistic priors. $\bar{R}$ is controlled directly by strategy design and is modelled as uniform over $[2, 3.5]$.

### 2.1 — Parameter Distributions

$$\bar{\omega} \sim \text{Beta}(\alpha, \beta), \quad \alpha = 5,\ \beta = 5.5$$

This yields a prior mean of:

$$\mathbb{E}[\bar{\omega}] = \frac{\alpha}{\alpha + \beta} = \frac{5}{10.5} \approx 0.476$$

with most probability mass concentrated between 40–55%, reflecting the honest expectation for a strategy that accepts lower win rates in exchange for higher reward ratios and leverage.

$$\bar{R} \sim \mathcal{U}(2, 3.5), \quad \mathbb{E}[\bar{R}] = 2.75$$

Since $\bar{R}$ is a design parameter — we set take-profit and stop-loss levels directly — uniform is appropriate here.

### 2.2 — Expected Base Growth Rate

With fixed parameters $S = 0.05$, $C = 10^6$, $L = 2$, $f_e = f_x = 0$, the fee term vanishes and the base growth rate reduces to:

$$G_1(\omega, \bar{R}) = \frac{S \cdot L}{1} \cdot (\omega(\bar{R}+1) - 1) = 0.1\,(\omega(\bar{R}+1) - 1)$$

The expected value over both distributions is:

$$\mathbb{E}[G_1] = \int_0^1 \int_2^{3.5} G_1(\omega, \bar{R}) \cdot \frac{1}{1.5} \cdot f_{\text{Beta}}(\omega;\, 5,\, 5.5) \, d\bar{R} \, d\omega$$

where:

$$f_{\text{Beta}}(\omega;\, 5,\, 5.5) = \frac{\omega^4 (1-\omega)^{4.5}}{B(5,\, 5.5)}$$

**Inner integral** over $\bar{R} \in [2,\ 3.5]$:

$$\int_2^{3.5} G_1(\omega, \bar{R}) \cdot \frac{1}{1.5}\, d\bar{R} = \frac{0.1}{1.5}\left[\omega\!\left(\frac{\bar{R}^2}{2} + \bar{R}\right) - \bar{R}\right]_2^{3.5}$$

$$= \frac{0.1}{1.5}\left[\omega(9.625 - 4.0) - (3.5 - 2.0)\right] = \frac{0.1}{1.5}(5.625\omega - 1.5)$$

$$= 0.1\,(3.75\omega - 1)$$

**Outer integral** over $\omega$:

$$\mathbb{E}[G_1] = \int_0^1 0.1\,(3.75\omega - 1) \cdot f_{\text{Beta}}(\omega;\, 5,\, 5.5)\, d\omega$$

$$= 0.1\,(3.75\,\mathbb{E}[\bar{\omega}] - 1) = 0.1\,\left(3.75 \times \frac{5}{10.5} - 1\right)$$

$$\boxed{\mathbb{E}[G_1] \approx 0.07857}$$

This clears $G_{\text{goal}} = 0.05$ by a margin of $0.02857$. The drag terms must fit within that margin.

### 2.3 — Win Rate Threshold

Setting $\mathbb{E}[G_1] = 0.05$ and solving for the minimum required prior mean:

$$0.1\,(3.75\,\mathbb{E}[\bar{\omega}] - 1) = 0.05$$

$$3.75\,\mathbb{E}[\bar{\omega}] = 1.5 \implies \mathbb{E}[\bar{\omega}]_{\min} = \frac{1.5}{3.75} = 0.400$$

**Any algorithm must achieve a backtested mean win rate of at least $40.0\%$.** Below this, $G_1$ cannot clear $G_{\text{goal}}$ even before drag is applied. Delta's tolerance for lower win rates — compared to Gamma's $50\%$ floor — is precisely what the higher $\bar{R}$ and leverage make possible.

### 2.4 — Volatility Ceiling

The drag terms $G_2$ and $G_3$ must satisfy:

$$G_2 + G_3 \geq -(\mathbb{E}[G_1] - G_{\text{goal}}) = -0.02857$$

Since $\sigma_\omega$ is a post-backtest quantity, we leave it symbolic and derive $\sigma_{\text{max}}$ as a function of $\sigma$ and $\sigma_\omega$:

$$\frac{\sigma^2}{2C^2} + \frac{\sigma_\omega^2 \cdot \Delta^2}{2C^2} \leq 0.02857$$

Using $\bar{R} = 2.75$ (prior mean), $S = 0.05$, $L = 2$, $C = 10^6$, $\Delta = S \cdot C \cdot L \cdot (\bar{R}+1) = 375{,}000$:

$$\sigma^2 + \sigma_\omega^2 \cdot \Delta^2 \leq 0.02857 \times 2C^2 = 5.714 \times 10^{10}$$

$$\boxed{\sigma_{\text{max}} = \sqrt{5.714 \times 10^{10} - \sigma_\omega^2 \cdot (375{,}000)^2}}$$

This is the **hard ceiling on per-trade P&L standard deviation** given any backtested $\sigma_\omega$. Once $n$ is known post-backtest, $\sigma_\omega = \sqrt{\frac{\bar{\omega}(1-\bar{\omega})}{n}}$ is substituted directly and the ceiling becomes concrete.

### 2.5 — Phase 2 Summary

| Constraint | Value |
|---|---|
| $\mathbb{E}[\bar{\omega}]_{\min}$ | $\geq 0.400$ |
| $\bar{R}$ range | $[2,\ 3.5]$, prior mean $= 2.75$ |
| $G_{\text{goal}}$ margin above $G_1$ | $0.02857$ |
| $\sigma_{\text{max}}$ | $\sqrt{5.714 \times 10^{10} - \sigma_\omega^2 \cdot (375{,}000)^2}$ |

The margin between $\mathbb{E}[G_1]$ and $G_{\text{goal}}$ is wide relative to Gamma's $0.00132$. This is a consequence of Delta's higher $S$ and $L$ — the strategy has more room to breathe on volatility drag, but any algorithm that falls below the $40\%$ win rate floor cannot be rescued by tighter parameters. Phase 3 must be designed to keep $\bar{\omega}$ reliably above $40\%$ even in difficult market conditions.

## 3. Designing the Strategy

### 3.1 — Timeframe Structure

| Role | Timeframe |
|---|---|
| Trend filter | 4H |
| Entry signal | 1H |

The 4H chart determines *whether* to trade. The 1H chart determines *when*. A valid 1H signal against the 4H trend is discarded unconditionally. Compared to Gamma's 1D/4H structure, Delta operates on shorter timeframes to generate more frequent signals — a deliberate trade-off: more trades, more opportunities, but also more noise exposure.

### 3.2 — Indicator Definitions

**Exponential Moving Average (EMA)** applies exponentially decreasing weights to historical prices, making it more responsive to recent price action than a simple moving average:

$$\text{EMA}_t = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_{t-1}, \quad \alpha = \frac{2}{n+1}$$

**Average True Range (ATR)** measures market volatility as the average of true ranges over a lookback period, where the true range accounts for gaps:

$$\text{TR}_t = \max(H_t - L_t,\ |H_t - C_{t-1}|,\ |L_t - C_{t-1}|)$$

$$\text{ATR}(n) = \frac{1}{n}\sum_{i=0}^{n-1} \text{TR}_{t-i}$$

**Average Directional Index (ADX)** measures trend strength independently of direction, ranging from 0 to 100. High ADX indicates a strong trend; low ADX indicates chop.

**Relative Strength Index (RSI)** measures momentum by comparing the magnitude of recent gains to losses, ranging from 0 to 100:

$$\text{RSI} = 100 - \frac{100}{1 + \frac{\text{avg gain}}{\text{avg loss}}}$$

### 3.3 — Indicators by Timeframe

**4H — Trend Filter**
- **EMA (100)** — macro trend direction. Price above = long-only bias. Price below = short-only bias.
- **ADX (14) > 20** — confirms trend conviction. Below 20, Delta sits flat.

**1H — Entry Signal**
- **EMA (21) / EMA (55) cross** — momentum shift in the direction of the 4H bias
- **ADX (14) > 15** — structural confirmation on the entry timeframe
- **RSI (14)** — momentum confirmation: RSI > 50 for longs, RSI < 50 for shorts

### 3.4 — Entry Conditions

**Long:**
1. 4H: Price > EMA (100) AND ADX > 20
2. 1H: EMA (21) crosses above EMA (55)
3. 1H: ADX > 15
4. 1H: RSI > 50

**Short:**
1. 4H: Price < EMA (100) AND ADX > 20
2. 1H: EMA (21) crosses below EMA (55)
3. 1H: ADX > 15
4. 1H: RSI < 50

All four conditions must be satisfied on candle close. One failing = no trade.

### 3.5 — Exit Conditions

- **Stop loss:** ATR (14) × 2.0 from entry, placed below the entry candle low (long) or above the entry candle high (short). The wider ATR multiplier compared to Gamma reflects the higher volatility inherent in leveraged futures on shorter timeframes.
- **Take profit:** SL distance × $\bar{R}$, backtested across $\bar{R} \in \{2.0,\ 2.5,\ 3.0,\ 3.5\}$ to identify the empirical optimum within the $\mathcal{U}(2, 3.5)$ prior from Phase 2
- **Hard invalidation:** 4H ADX drops below 20 mid-trade → close at market

### 3.6 — Risk Management

- Position size $S = 0.05$, capital $C = \$1{,}000{,}000$, leverage $L = 2$ per Phase 1 — fixed, no deviation
- No pyramiding
- Maximum 1 open position per pair at any time
- Universe: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT futures on Kraken

### 3.7 — Design Notes

Delta's shift to futures introduces funding rate exposure absent in Gamma's spot trading. Kraken's zero maker fee policy eliminates transaction cost drag, but funding rates on leveraged futures positions must be monitored post-deployment — they are not modelled in the current $G$ framework and constitute an unaccounted drag term.

The shorter 4H/1H timeframe structure relative to Gamma's 1D/4H will produce significantly more trade signals, which is desirable: more trades reduce $\sigma_\omega$ (win rate uncertainty drag decreases as $n$ grows), while also providing the statistical sample size needed to validate the $40\%$ win rate floor with confidence.

If backtesting yields insufficient trades, the first adjustment is relaxing the 4H ADX threshold to 15 before modifying any other parameter.
