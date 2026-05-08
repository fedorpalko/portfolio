## Thesis

**Theta ($\Theta$)** is a high-risk, high-reward trading strategy designed for individuals who can tolerate significant volatility and the complete wipe of capital, targeting an extremely high $G$ to maximize potential profits. It is grounded in the [Universal Growth Rate Model](../EV_paper.md) and is, like all strategies in the pipeline, derived from Gamma — but taken to a degenerate extreme on purpose.

> **Warning:** this strategy is highly experimental and not recommended for use. The only reason for its existence is to test the limits of the [Universal Growth Rate Model](../EV_paper.md) and to understand how it handles extreme cases, as well as attempting to demonstrate that a sufficiently precise algorithm can perform what amounts to real-life financial alchemy — even if it cannot exist in the frictionless real world.

## Development Plan

1. Defining strategy scope
2. Deploying $G$ and locating the thresholds for $\bar{\omega}$, $\bar{R}$ and $\sigma$
3. Designing the strategy
4. Implementing the strategy
5. Backtesting the strategy
6. Validating the strategy
7. Conclusion

## 1. Defining Strategy Scope

Theta's sole goal is to turn a small account into a significantly larger one through compounding at an extreme per-trade growth rate. Unlike Gamma, which relies on trend following and strict drawdown control, Theta deliberately discards the safety net. It does not follow trends — it exploits **short-term mean reversion and volatility events** on the 1H timeframe, taking exactly one trade per day.

The key insight: trend-following strategies need high $\bar{R}$ and accept lower $\bar{\omega}$. Theta flips this — it targets a **higher $\bar{\omega}$** by fading overextended moves and capturing predictable snap-backs, accepting a moderate $\bar{R}$ in exchange. This is the only way to mechanically achieve $G \geq 0.027$ with leverage on a small account.

- Position sizing $S = 0.25$ (25% of capital per trade — this is not a typo)
- Capital is defined as $C = 200$
- Fee structure is defined as $f_e = f_x = 0.0002$ (Bitget limit order maker fee, 0.02%)
- Leverage is set at $L = 5$
- We are trading futures pairs using limit orders on Bitget
- **Target growth rate:** $G_{\text{goal}} = 0.027$ per trade
- **Target trajectory:** $\$200 \to \approx \$40{,}000$ in $N = 200$ trades

### 1.1 — Why G = 0.027?

The compounding math is unambiguous:

$$C_N = C_0 \cdot (1 + G)^N$$

At $G = 0.027$ and $N = 200$:

$$C_{200} = 200 \cdot (1.027)^{200} \approx 200 \cdot 206 = \$41{,}200$$

This is the closest value to the $\$40{,}000$ target achievable with a round $G$ figure. Higher values of $G$ overshoot dramatically:

| $G$ | $(1+G)^{200}$ | $C_{200}$ |
|-----|--------------|-----------|
| 0.025 | ~140 | ~$28,000 |
| **0.027** | **~206** | **~$41,200** ✓ |
| 0.030 | ~369 | ~$73,800 |
| 0.035 | ~968 | ~$193,600 |
| 0.045 | ~6,640 | ~$1,328,000 |

$G_{\text{goal}} = 0.027$ is the honest number. It's still insane by any objective standard.

---

## 2. Deploying $G$ and Locating the Thresholds for $\bar{\omega}$, $\bar{R}$ and $\sigma$

The goal of this phase is to determine the minimum parameter constraints that any algorithm implementing Theta must satisfy to guarantee $\mathbb{E}[G] \geq G_{\text{goal}} = 0.027$.

### 2.1 — The UGRM for Theta

The Universal Growth Rate is defined as:

$$G = G_1 - G_2 - G_3$$

where:

$$G_1 = \frac{\rho}{C}, \quad G_2 = \frac{\sigma^2}{2C^2}, \quad G_3 = \frac{\sigma_\omega^2 \cdot \Delta^2}{2C^2}$$

and the raw expected value per trade is:

$$\rho = \omega \cdot S \cdot C \cdot L \cdot \bar{R} - (1 - \omega) \cdot S \cdot C \cdot L - (f_e + f_x) \cdot S \cdot C \cdot L$$

With Theta's fixed parameters ($S = 0.25$, $C = 200$, $L = 5$, $f_e = f_x = 0.0002$), the effective position exposure is:

$$E = S \cdot C \cdot L = 0.25 \times 200 \times 5 = \$250$$

and the fee term is:

$$f_{\text{total}} \cdot E = (0.0002 + 0.0002) \times 250 = \$0.10$$

This gives:

$$\rho = 250\omega\bar{R} - 250(1-\omega) - 0.10 = 250(\omega(\bar{R}+1) - 1) - 0.10$$

and the base growth rate:

$$G_1 = \frac{\rho}{C} = \frac{250(\omega(\bar{R}+1) - 1) - 0.10}{200} = 1.25(\omega(\bar{R}+1) - 1) - 0.0005$$

### 2.2 — Parameter Distributions

Theta is a **mean reversion** strategy, not a trend follower. Mean reversion on short intraday timeframes typically yields higher win rates with lower reward ratios — the trade snaps back quickly or it doesn't. This justifies a fundamentally different prior from Gamma.

$$\bar{\omega} \sim \text{Beta}(\alpha, \beta), \quad \alpha = 7,\ \beta = 4$$

This yields a prior mean of:

$$\mathbb{E}[\bar{\omega}] = \frac{\alpha}{\alpha + \beta} = \frac{7}{11} \approx 0.636$$

with probability mass concentrated between 50–80%, reflecting a realistic expectation for a disciplined mean-reversion system on high-liquidity crypto pairs. Mean reversion has a structural edge when RSI-extremes and volume spikes are used correctly — 63.6% is aggressive but not delusional.

$$\bar{R} \sim \mathcal{U}(1, 2), \quad \mathbb{E}[\bar{R}] = 1.5$$

We target a tighter $\bar{R}$ range compared to Gamma. Mean reversion trades are taken with a modest reward target — the move is captured before it reverses again. $\bar{R} \in [1, 2]$ is the realistic range for this style.

### 2.3 — Expected Base Growth Rate

With $E = \$250$, $C = 200$, the fee contribution is negligible ($\$0.10$ per trade). Dropping it for the analytical derivation:

$$G_1(\omega, \bar{R}) \approx 1.25(\omega(\bar{R}+1) - 1)$$

Taking the expectation over both distributions:

$$\mathbb{E}[G_1] = \int_0^1 \int_1^2 1.25(\omega(\bar{R}+1) - 1) \cdot \frac{1}{1} \cdot f_{\text{Beta}}(\omega;\,7,\,4)\, d\bar{R}\, d\omega$$

**Inner integral** over $\bar{R} \in [1, 2]$ (uniform, so $\frac{1}{1}$ density):

$$\int_1^2 (\omega(\bar{R}+1) - 1)\, d\bar{R} = \omega \int_1^2 (\bar{R}+1)\, d\bar{R} - 1$$

$$= \omega \left[\frac{\bar{R}^2}{2} + \bar{R}\right]_1^2 - 1 = \omega\left[(2 + 2) - (0.5 + 1)\right] - 1 = \omega \cdot 2.5 - 1$$

So:

$$\mathbb{E}[G_1] = \int_0^1 1.25(2.5\omega - 1) \cdot f_{\text{Beta}}(\omega;\, 7,\, 4)\, d\omega$$

$$= 1.25\left(2.5\,\mathbb{E}[\bar{\omega}] - 1\right) = 1.25(2.5 \times 0.636 - 1)$$

$$= 1.25(1.591 - 1) = 1.25 \times 0.591$$

$$\boxed{\mathbb{E}[G_1] \approx 0.0739}$$

This clears $G_{\text{goal}} = 0.027$ by a margin of $0.0469$. The drag terms must fit within that margin.

> Note: the margin is large relative to Gamma. This is expected — Theta uses $25\times$ more position sizing as a fraction of capital with $5\times$ leverage, so $G_1$ is structurally larger. The drag terms $G_2$ and $G_3$ will also be significantly larger than Gamma's. The margin is wide enough to absorb them, but not unconditionally so — see §2.5.

### 2.4 — Win Rate Threshold

Setting $\mathbb{E}[G_1] = G_{\text{goal}} = 0.027$ and solving for the minimum required prior mean:

$$1.25(2.5\,\mathbb{E}[\bar{\omega}]_{\min} - 1) = 0.027$$

$$2.5\,\mathbb{E}[\bar{\omega}]_{\min} = \frac{0.027}{1.25} + 1 = 0.0216 + 1 = 1.0216$$

$$\mathbb{E}[\bar{\omega}]_{\min} = \frac{1.0216}{2.5} = 0.4086$$

$$\boxed{\mathbb{E}[\bar{\omega}]_{\min} \geq 0.409}$$

**Any algorithm must achieve a backtested mean win rate of at least $40.9\%$.** This threshold is lower than Gamma's 50.0% because Theta's structural leverage and position sizing provide a much larger $G_1$ coefficient. That said, don't be fooled — a 41% win rate with $\bar{R} = 1.5$ is the absolute floor. Anything below that and you're not gambling, you're just handing money to the exchange.

### 2.5 — Volatility Ceiling

With Theta's parameters, the P&L on any single trade swings hard. A winning trade at $\bar{R} = 1.5$ nets $0.25 \times 200 \times 5 \times 1.5 = \$375$. A losing trade costs $\$250$. With a 200-trade sequence this produces extreme variance in the capital trajectory.

The drag terms must satisfy:

$$G_2 + G_3 \leq \mathbb{E}[G_1] - G_{\text{goal}} = 0.0739 - 0.027 = 0.0469$$

**Drag term $G_2$** (volatility drag):

$$G_2 = \frac{\sigma^2}{2C^2} \leq 0.0469$$

$$\sigma^2 \leq 0.0469 \times 2 \times 200^2 = 0.0469 \times 80{,}000 = 3{,}752$$

$$\boxed{\sigma_{\text{max}} \approx \$61.25 \text{ (ignoring } G_3)}$$

**Drag term $G_3$** (win rate uncertainty):

$$G_3 = \frac{\sigma_\omega^2 \cdot \Delta^2}{2C^2}$$

where $\Delta = S \cdot C \cdot L \cdot (\bar{R} + 1)$. At $\bar{R} = 1.5$:

$$\Delta = 0.25 \times 200 \times 5 \times 2.5 = \$625$$

Post-backtest, $\sigma_\omega = \sqrt{\frac{\omega(1-\omega)}{n}}$, so with $\omega = 0.636$ and $n = 200$:

$$\sigma_\omega = \sqrt{\frac{0.636 \times 0.364}{200}} = \sqrt{0.001158} \approx 0.03403$$

$$G_3 = \frac{(0.03403)^2 \times (625)^2}{2 \times (200)^2} = \frac{0.001158 \times 390{,}625}{80{,}000} = \frac{452.3}{80{,}000} \approx 0.00565$$

**Combined ceiling accounting for both drags:**

$$G_2 \leq 0.0469 - G_3 = 0.0469 - 0.00565 = 0.04125$$

$$\sigma^2 \leq 0.04125 \times 80{,}000 = 3{,}300$$

$$\boxed{\sigma_{\text{max}} \approx \$57.45}$$

This is a hard bound given the prior mean win rate and $n = 200$. Expressed as a general function:

$$\boxed{\sigma_{\text{max}} = \sqrt{0.04125 \times 2C^2 - \sigma_\omega^2 \cdot \Delta^2}}$$

where $\sigma_\omega$ and $\Delta$ are substituted from backtest results.

> **Context:** $\sigma_{\text{max}} \approx \$57$ sounds tight. It isn't unreasonable for a mean reversion strategy on 1H with defined TP/SL — individual trade P&L is either $+\$375$ or $-\$250$ with some variation around those fixed levels depending on slippage. The actual empirical $\sigma$ will be computed in Phase 5.

### 2.6 — Phase 2 Summary

| Constraint | Value |
|---|---|
| $G_{\text{goal}}$ | $0.027$ per trade |
| $\mathbb{E}[\bar{\omega}]_{\min}$ | $\geq 0.409$ |
| $\bar{R}$ range | $[1,\ 2]$, prior mean $= 1.5$ |
| $\bar{\omega}$ prior | $\text{Beta}(7, 4)$, mean $= 0.636$ |
| $\mathbb{E}[G_1]$ | $\approx 0.0739$ |
| Margin above $G_{\text{goal}}$ | $0.0469$ |
| $\Delta$ at prior mean $\bar{R}$ | $\$625$ |
| $G_3$ at $n = 200$, $\omega = 0.636$ | $\approx 0.00565$ |
| $\sigma_{\text{max}}$ | $\approx \$57.45$ |

The win rate floor is lower than Gamma's, but that's structural — the leverage and position size do the heavy lifting on $G_1$. The real constraint is $\sigma$. Since every trade either wins $\approx \$375$ or loses $\approx \$250$, keeping empirical $\sigma$ near the ceiling requires the TP/SL to be **fixed and clean** with minimal slippage. Any implementation that allows partial fills or loose limit placement will blow through this ceiling immediately.

The compounding trajectory toward $\$40{,}000$ is mathematically valid. It is not, however, forgiving. A 5-trade losing streak at $S = 0.25$ sheds $\approx 72\%$ of capital from peak. That's not a bug, that's the strategy.

---

## 3. Designing the Strategy

### 3.1 — Timeframe Structure

| Role | Timeframe |
|---|---|
| Signal generation + execution | 1H |

Theta operates on a **single timeframe: 1H.** There is no higher-timeframe bias filter. The rationale is structural: highly volatile crypto futures pairs (BTC/USDT, ETH/USDT) exhibit short-term mean reversion at the 1H level that is largely independent of 4H or daily context. Adding a higher-timeframe trend filter would, paradoxically, destroy the strategy — mean reversion entries are by definition counter to the prevailing short-term trend, and a 4H trend filter would suppress exactly the setups we want. One timeframe. One decision layer.

The 1-trade-per-day constraint is enforced mechanically: once a trade is triggered and resolved on any given calendar day (UTC), no further entries are taken regardless of signal quality. This is a regime gate, not a market gate.

### 3.2 — Indicator Definitions

**Relative Strength Index (RSI)** measures the speed and magnitude of recent price changes, ranging from 0 to 100:

$$\text{RSI} = 100 - \frac{100}{1 + RS}, \quad RS = \frac{\text{Avg Gain}_{n}}{\text{Avg Loss}_{n}}$$

We use a **9-period RSI** instead of the standard 14. On 1H candles, RSI(14) reacts too slowly — extreme readings that represent genuine exhaustion are already partially resolved by the time they print. RSI(9) is more reactive and better suited to catching the actual capitulation candle.

**Bollinger Bands** are a volatility envelope placed at $k$ standard deviations above and below a moving average:

$$\text{BB}_{\text{upper}} = \text{MA}(n) + k \cdot \sigma_n, \quad \text{BB}_{\text{lower}} = \text{MA}(n) - k \cdot \sigma_n$$

We use the standard **BB(20, 2)** — 20-period SMA with $k = 2$ standard deviation bands. Three components matter here:

- **Lower band** — defines the overextension zone for long entries
- **Upper band** — defines the overextension zone for short entries  
- **Midline (SMA 20)** — this is the **take-profit target** for all trades; it represents the mean price is reverting toward

**Relative Volume (RVOL)** normalises current-candle volume against the rolling average over the prior $n$ periods:

$$\text{RVOL} = \frac{V_{\text{current}}}{\text{MA}_{\text{vol}}(n)}$$

We use **RVOL(20)** with a spike threshold of $\theta_{\text{vol}} = 2.0$. An RVOL reading above 2.0 on the entry candle means volume is at least double the 20-candle average — this is the exhaustion signal. A price move to the BB boundary on low volume is just drift; the same move on a volume spike is capitulation. We only trade the latter.

**Average Directional Index (ADX)** measures trend strength, ranging from 0 (no trend) to 100 (extreme trend), direction-agnostic:

$$\text{ADX} = \text{MA}\left(\frac{|+DI - {-DI}|}{+DI + {-DI}} \times 100\right)$$

We use **ADX(14) as an exclusion filter**. This is the inverse of Gamma's usage: where Gamma requires ADX > 25 to confirm trend strength, Theta requires **ADX < 25** to confirm the *absence* of a strong trend. Mean reversion inside a powerful trend is one of the fastest ways to get liquidated at $L = 5$. ADX < 25 ensures we operate in the ranging or weakly-trending environments where mean reversion has structural validity.

### 3.3 — Entry Conditions

All conditions are evaluated on **candle close** at the 1H timeframe. One failing condition = no trade. No exceptions.

**Long (fade the dip):**
1. Price closes **at or below** the BB lower band: $\text{Close} \leq \text{BB}_{\text{lower}}$
2. RSI(9) $< 30$ — oversold reading confirming exhaustion
3. RVOL(20) $\geq 2.0$ — volume spike confirming capitulation, not slow drift
4. ADX(14) $< 25$ — no strong downtrend present; price is overextended, not trending

**Short (fade the rally):**
1. Price closes **at or above** the BB upper band: $\text{Close} \geq \text{BB}_{\text{upper}}$
2. RSI(9) $> 70$ — overbought reading confirming exhaustion
3. RVOL(20) $\geq 2.0$ — volume spike confirming euphoric blow-off, not slow grind
4. ADX(14) $< 25$ — no strong uptrend present

All four conditions are **conjunctive** — required simultaneously. The filter stack is intentionally restrictive. With a 1-trade-per-day cap, missed setups are not a problem; false positives are. A single bad trade at $S = 0.25$ with $L = 5$ costs 25% of capital. Signal quality is the only currency that matters.

> **On signal frequency:** It is expected that on many days, no valid signal fires. This is correct behaviour. Do not loosen the conditions to force a daily trade. The 1-trade-per-day cap is a maximum, not a quota.

### 3.4 — Exit Conditions

**Take Profit:** The BB midline (SMA 20) at the time of entry, treated as a fixed target from entry. It is calculated at entry and does not move as price evolves — this prevents the midline drifting against us mid-trade from changing the effective R̄.

$$\text{TP} = \text{SMA}_{20}\big|_{t_{\text{entry}}}$$

**Stop Loss:** Placed at $1 \times$ the BB band distance beyond the entry point. Concretely:

$$\text{SL}_{\text{long}} = \text{Close} - (\text{BB}_{\text{lower}} - \text{BB}_{\text{lower}}) \to \text{Close} - \delta$$

where $\delta$ is calibrated during backtesting as the median distance from entry close to the band boundary on valid signals. In practice: a fixed ATR(14)-based stop of **1.5 × ATR** below entry for longs, above entry for shorts, is the implementation default until backtest results suggest a tighter calibration.

$$\text{SL}_{\text{long}} = \text{Entry} - 1.5 \times \text{ATR}(14)$$
$$\text{SL}_{\text{short}} = \text{Entry} + 1.5 \times \text{ATR}(14)$$

This makes $\bar{R}$ dynamic per-trade (distance to midline / ATR-based SL), which is precisely why $\bar{R} \sim \mathcal{U}(1, 2)$ was chosen as a prior rather than a fixed value. Backtesting will reveal the empirical distribution.

**Hard invalidation:** If after entry the BB midline moves *away* from price by more than $2 \times$ ATR (price continues trending hard in the wrong direction), the trade is closed at market. This is a secondary safety valve for the scenario where a ranging market suddenly breaks into trend during the trade.

### 3.5 — Risk Management

- Position size $S = 0.25$ per Phase 1 — fixed, no deviation, no discretionary scaling
- Capital compounds trade-to-trade: $C_{t+1} = C_t + \text{PnL}_t$. This is the mechanism that drives $\$200 \to \$40{,}000$ — without compounding, Theta is just a high-variance coin flip
- Maximum **1 open position** at any time across all pairs
- No pyramiding, no averaging down into a loss
- Universe: **BTC/USDT, ETH/USDT** perpetual futures on Bitget, limit orders only
- If no signal fires by 22:00 UTC, no trade is taken that day. The day is skipped.

### 3.6 — Indicator Interaction and Design Rationale

The four indicators are genuinely complementary rather than overlapping:

- **RSI(9)** operates on price momentum — it asks *how hard* the move was
- **Bollinger Bands(20, 2)** operate on statistical price distribution — they ask *how far from normal* the price is
- **RVOL(20)** operates on market participation — it asks *how many people were involved*
- **ADX(14)** operates on trend structure — it asks *is this a ranging or trending environment*

Each answers a different question. A signal requires all four to align, which means: price has moved statistically far from its mean (BB), momentum is extreme (RSI), the move was driven by real volume and not just thin air (RVOL), and there's no structural trend absorbing the reversion potential (ADX). That conjunction describes exactly one scenario: an exhaustion spike in a choppy market, which is the highest-probability mean reversion setup available on 1H crypto data.

### 3.7 — Design Summary

| Parameter | Value |
|---|---|
| Timeframe | 1H only |
| Max trades per day | 1 |
| Long entry | Close ≤ BB lower AND RSI(9) < 30 AND RVOL ≥ 2× AND ADX < 25 |
| Short entry | Close ≥ BB upper AND RSI(9) > 70 AND RVOL ≥ 2× AND ADX < 25 |
| Take profit | BB midline (SMA 20) at entry, fixed |
| Stop loss | 1.5 × ATR(14) from entry |
| Pairs | BTC/USDT, ETH/USDT perpetual futures |
| Exchange | Bitget, limit orders |
| Position size | $S = 0.25$ (compounding) |
| Leverage | $L = 5$ |
