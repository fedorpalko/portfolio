## Thesis

**Gamma ($\gamma$)** is a trading strategy grounded and built upon the rigorous [Universal Growth Rate Model](../EV_paper.md). The strategy is designed for portfolio managers and institutions that seek to use large amounts of capital to generate a steady return with minimal drawdowns and the ability to benefit from both up and down market movements via trend following on various large cryptocurrency pairs.

It utilizes integration and $G$ to find minimal values of win rate, reward and volatility for an acceptable return rate and growth factor and therefore determine whether the strategy is mathematically viable.

## Development Plan

1. Defining strategy scope
2. Deploying $G$ and locating the thresholds for $\bar{\omega}$, $\bar{R}$ and $\sigma$
3. Designing the strategy
4. Implementing the strategy
5. Backtesting the strategy
6. Refining the strategy
7. Conclusion

## 1. Defining Strategy Scope

Gamma's main goal is to generate profit by following trends in the market. It aims to make money in bullish and bearish periods, while minimizing losses in sideways/choppy periods thanks to strong ADX filters. ADX is chosen because it allows to detect weak trends and filter them out, as to not lose money in choppy markets, which would cause "*death by a thousand cuts*".

- Position sizing is determined via $S = 0.02$ to match standard institutional requirements
- Capital is defined as $C = 1,000,000\$$
- Fees are defined as $f_e = f_x = 0$ due to Binance.US's zero maker fee policy on limit orders
- Leverage is set at $L=1$
- We are trading spot pairs using limit orders on Binance.US

## 2. Deploying $G$ and Locating the Thresholds

The goal of this phase is to determine the minimum parameter constraints that any algorithm implementing Gamma must satisfy to guarantee $\mathbb{E}[G] \geq G_{\text{goal}} = 0.01$.

Since $\bar{\omega}$ is unknown prior to backtesting and not uniformly distributed — a 30% win rate is far more plausible than a 90% win rate for a trend-following strategy — we model it using a **Beta distribution**, which is defined on $(0, 1)$ and flexible enough to encode realistic priors. $\bar{R}$ is controlled directly by strategy design and is therefore modelled as uniform over $[1, 3]$.

### 2.1 — Parameter Distributions

$$\bar{\omega} \sim \text{Beta}(\alpha, \beta), \quad \alpha = 6,\ \beta = 5.5$$

This yields a prior mean of:

$$\mathbb{E}[\bar{\omega}] = \frac{\alpha}{\alpha + \beta} = \frac{6}{11.5} \approx 0.522$$

with most probability mass concentrated between 40–68%, reflecting a moderate but honest expectation for a crypto trend follower.

$$\bar{R} \sim \mathcal{U}(1, 3), \quad \mathbb{E}[\bar{R}] = 2$$

Since $\bar{R}$ is a design parameter — we set the take-profit and stop-loss levels directly — uniform is appropriate here.

### 2.2 — Expected Base Growth Rate

With fixed parameters $S = 0.02$, $C = 10^6$, $L = 1$, $f_e = f_x = 0$, the fee term vanishes and the base growth rate reduces to:

$$G_1(\omega, \bar{R}) = 0.02(\omega\bar{R} + \omega - 1)$$

The expected value over both distributions is:

$$\mathbb{E}[G_1] = \int_0^1 \int_1^3 G_1(\omega, \bar{R}) \cdot \frac{1}{2} \cdot f_{\text{Beta}}(\omega;\, 6,\, 5.5) \, d\bar{R} \, d\omega$$

where:

$$f_{\text{Beta}}(\omega;\, 6,\, 5.5) = \frac{\omega^5 (1-\omega)^{4.5}}{B(6,\, 5.5)}$$

**Inner integral** over $\bar{R} \in [1,3]$:

$$\int_1^3 G_1(\omega, \bar{R}) \cdot \frac{1}{2}\, d\bar{R} = \frac{1}{2}(0.12\omega - 0.04)$$

**Outer integral** over $\omega$:

$$\mathbb{E}[G_1] = \int_0^1 \frac{1}{2}(0.12\omega - 0.04) \cdot f_{\text{Beta}}(\omega;\, 6,\, 5.5)\, d\omega$$

$$= \frac{0.12}{2}\,\mathbb{E}[\bar{\omega}] - \frac{0.04}{2}$$

$$= 0.06 \times 0.522 - 0.02$$

$$\boxed{\mathbb{E}[G_1] \approx 0.01132}$$

This clears $G_{\text{goal}} = 0.01$ by a margin of $0.00132$. The drag terms must fit within that margin.

### 2.3 — Win Rate Threshold

Setting $\mathbb{E}[G_1] = 0.01$ and solving for the minimum required prior mean:

$$0.06\,\mathbb{E}[\bar{\omega}] - 0.02 = 0.01$$

$$\mathbb{E}[\bar{\omega}]_{\min} = \frac{0.03}{0.06} = 0.500$$

**Any algorithm must achieve a backtested mean win rate of at least $50.0\%$.** Below this, $G_1$ cannot clear $G_{\text{goal}}$ even before drag is applied.

### 2.4 — Volatility Ceiling

The drag terms $G_2$ and $G_3$ must satisfy:

$$G_2 + G_3 \geq -(\mathbb{E}[G_1] - G_{\text{goal}}) = -0.00132$$

Since $\sigma_\omega$ is a post-backtest quantity, we leave it symbolic and derive $\sigma_{\text{max}}$ as a function of $\sigma$ and $\sigma_\omega$:

$$\frac{\sigma^2}{2C^2} + \frac{\sigma_\omega^2 \cdot (S \cdot C \cdot (\bar{R}+1))^2}{2C^2} \leq 0.00132$$

Using $\bar{R} = 2$ (prior mean), $S = 0.02$, $C = 10^6$, $\Delta = S \cdot C \cdot (\bar{R}+1) = 60{,}000$:

$$\sigma^2 + \sigma_\omega^2 \cdot \Delta^2 \leq 0.00132 \times 2C^2 = 2.64 \times 10^9$$

$$\boxed{\sigma_{\text{max}} = \sqrt{2.64 \times 10^9 - \sigma_\omega^2 \cdot (60{,}000)^2}}$$

This is the **hard ceiling on per-trade P&L standard deviation** given any backtested $\sigma_\omega$. Once $n$ is known post-backtest, $\sigma_\omega = \sqrt{\frac{\bar{\omega}(1-\bar{\omega})}{n}}$ is substituted directly and the ceiling becomes concrete.

### 2.5 — Phase 2 Summary

| Constraint | Value |
|---|---|
| $\mathbb{E}[\bar{\omega}]_{\min}$ | $\geq 0.500$ |
| $\bar{R}$ range | $[1,\ 3]$, prior mean $= 2$ |
| $G_{\text{goal}}$ margin above $G_1$ | $0.00132$ |
| $\sigma_{\text{max}}$ | $\sqrt{2.64 \times 10^9 - \sigma_\omega^2 \cdot \Delta^2}$ |

The margin between $\mathbb{E}[G_1]$ and $G_{\text{goal}}$ is intentionally tight. This is a feature, not a flaw — it means the strategy has no room to tolerate a sloppy algorithm. Phase 3 must be designed to push $\bar{\omega}$ meaningfully above $0.500$, giving the drag terms room to breathe.

## 3. Designing the Strategy

### 3.1 — Timeframe Structure

| Role | Timeframe |
|---|---|
| Trend filter | 1D |
| Entry signal | 4H |

The 1D chart determines *whether* to trade. The 4H chart determines *when.* A valid 4H signal against the 1D trend is discarded unconditionally.

### 3.2 — Indicator Definitions

**Triple Exponential Moving Average (TEMA)** reduces lag relative to a standard EMA by applying triple smoothing:

$$\text{TEMA} = 3 \cdot \text{EMA}_1 - 3 \cdot \text{EMA}_2 + \text{EMA}_3$$

where $\text{EMA}_2 = \text{EMA}(\text{EMA}_1)$ and $\text{EMA}_3 = \text{EMA}(\text{EMA}_2)$.

**Chande Momentum Oscillator (CMO)** measures momentum across all price movement, ranging from $-100$ to $+100$:

$$\text{CMO} = 100 \cdot \frac{\sum U - \sum D}{\sum U + \sum D}$$

where $\sum U$ is the sum of upward closes and $\sum D$ the sum of downward closes over a 14-period lookback.

### 3.3 — Indicators by Timeframe

**1D — Trend Filter**
- **TEMA (200)** — macro trend direction. Price above = long-only bias. Price below = short-only bias.
- **ADX (14) > 25** — confirms trend conviction. Below 25, Gamma sits flat — no entries in either direction.

**4H — Entry Signal**
- **TEMA (21) / TEMA (50) cross** — momentum shift in the direction of the 1D bias
- **ADX (14) > 20** — structural confirmation on the entry timeframe
- **CMO (14) zero-cross** — CMO crosses above 0 for longs, below 0 for shorts

### 3.4 — Entry Conditions

**Long:**
1. 1D: Price > TEMA (200) AND ADX > 25
2. 4H: TEMA (21) crosses above TEMA (50)
3. 4H: ADX > 20
4. 4H: CMO crosses above 0

**Short:**
1. 1D: Price < TEMA (200) AND ADX > 25
2. 4H: TEMA (21) crosses below TEMA (50)
3. 4H: ADX > 20
4. 4H: CMO crosses below 0

All four conditions must be satisfied on candle close. One failing = no trade.

### 3.5 — Exit Conditions

- **Stop loss:** ATR (14) × 1.5 from entry, placed below the entry candle low (long) or above the entry candle high (short)
- **Take profit:** SL distance × $\bar{R}$, backtested across $\bar{R} \in \{1.5, 2.0, 2.5, 3.0\}$ to identify the empirical optimum within the $\mathcal{U}(1, 3)$ prior from Phase 2
- **Hard invalidation:** 1D ADX drops below 25 mid-trade → close at market

### 3.6 — Risk Management

- Position size $S = 0.02$, capital $C = \$1{,}000{,}000$ per Phase 1 — fixed, no deviation
- No pyramiding
- Maximum 1 open position per pair at any time
- Universe: BTC/USDT, ETH/USDT spot pairs on Binance.US

### 3.7 — Design Notes

The TEMA and CMO indicators are both momentum-sensitive and will frequently signal simultaneously on strong trending candles. This is intentional — the filter stack is self-reinforcing by design. ADX provides the orthogonal layer, measuring trend *strength* independently of direction or momentum. The three indicators are genuinely complementary rather than redundant.

If backtesting yields insufficient trades for a statistically meaningful $\sigma_\omega$, the first adjustment is widening the CMO filter to a $\pm 10$ band before modifying any other parameter.

## 4. Implementing the Strategy

This one really doesn't warrant its own section, but you can find the code right [here](Gamma.py).
