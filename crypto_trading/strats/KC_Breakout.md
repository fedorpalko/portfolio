# Keltner Channel Breakout Strategy

> **Status:** Pre-implementation — mathematical foundation complete, backtesting pending.

---

## Thesis

Before writing a single line of code, the strategy was grounded mathematically. The goal was to derive a theoretically justified R:R target from first principles, rather than picking one arbitrarily or reverse-engineering it from backtest results. The reason for that is to avoid overfitting to the specific backtest.

The development followed this sequence:

1. **Define the EV model** — express expected value per trade as a function of win rate and reward:risk ratio
2. **Treat win rate as uncertain** — model it as a distribution over a realistic range rather than a point estimate
3. **Integrate over that distribution** — derive the expected EV analytically
4. **Solve for the optimal R** — find the reward:risk ratio that maximises expected EV given the assumed win rate range
5. **Use the result to constrain strategy design** — TP placement, SL placement, and entry selectivity all follow from the math

In terms of the code, it's located [here](ft/user_data/strategies/KC_Breakout.py)

---

## Phase 1 — Mathematical Foundation

### 1.1 The EV Model

For a single trade with stake $X$, win rate $w$, and reward:risk ratio $R$:

$$EV(w, R) = X \cdot [w \cdot R - (1 - w)]$$

Where:
- $w \in [0, 1]$ — probability of a winning trade
- $R$ — ratio of profit to loss on a single trade (e.g. $R = 3$ means TP is 3× the SL distance)
- $X$ — capital at risk per trade (fixed stake)

The breakeven condition $EV = 0$ gives:

$$w \cdot R = 1 - w \implies R^* = \frac{1 - w}{w}$$

Any $R > R^*$ yields positive expectancy.

---

### 1.2 Treating Win Rate as a Distribution

A backtested win rate is a point estimate with uncertainty. Rather than assuming $w$ is known exactly, it is modelled as a uniform random variable over a realistic range $[w_{lo},\ w_{hi}]$:

$$w \sim \mathcal{U}(w_{lo},\ w_{hi}), \quad f(w) = \frac{1}{w_{hi} - w_{lo}}$$

This is a conservative, minimally-informative prior. It says: *the true win rate lies somewhere in this interval, and we make no further assumption about where.*

A Beta distribution would be more precise once backtest sample size is known, and will replace this prior in a later iteration.

---

### 1.3 The Integral — Deriving Expected EV

The expected value of $EV$ over the win rate distribution, for a fixed $R$:

$$\mathbb{E}[EV(R)] = X \cdot \int_{w_{lo}}^{w_{hi}} \left[ wR - (1 - w) \right] \cdot \frac{1}{w_{hi} - w_{lo}}\ dw$$

Expanding:

$$= \frac{X}{w_{hi} - w_{lo}} \cdot \int_{w_{lo}}^{w_{hi}} \left[ w(R + 1) - 1 \right]\ dw$$

Evaluating:

$$\int_{w_{lo}}^{w_{hi}} \left[ w(R+1) - 1 \right] dw = (R+1) \cdot \frac{w_{hi}^2 - w_{lo}^2}{2} - (w_{hi} - w_{lo})$$

$$= (w_{hi} - w_{lo}) \left[ (R+1) \cdot \frac{w_{hi} + w_{lo}}{2} - 1 \right]$$

The $(w_{hi} - w_{lo})$ cancels with the denominator, leaving the **closed form**:

$$\boxed{\mathbb{E}[EV(R)] = X \cdot \left[ \bar{w} \cdot R - (1 - \bar{w}) \right]}$$

where $\bar{w} = \dfrac{w_{lo} + w_{hi}}{2}$ is the midpoint of the win rate range.

**Interpretation:** under a uniform prior, the integral reduces exactly to the EV formula evaluated at the mean win rate. The width of the uncertainty range does not affect the expected EV — only the centre matters. This is mathematically clean and justifies using $\bar{w}$ as the design parameter.

---

### 1.4 Optimal R and Parameter Targets

For a breakout sniper strategy, a realistic win rate range is estimated at:

$$w \in [0.35,\ 0.50], \quad \bar{w} = 0.425$$

**Breakeven R:**

$$R^* = \frac{1 - \bar{w}}{\bar{w}} = \frac{0.575}{0.425} \approx 1.35$$

Any $R > 1.35$ produces positive expected EV. However, at small capital ($X = €500$), fee drag erodes this margin. Accounting for approximately $0.12\%$ round-trip fees on Bitget futures:

$$EV_{net}(R) = X \cdot \left[ \bar{w} \cdot R - (1 - \bar{w}) \right] - 2 \cdot f \cdot X$$

where $f \approx 0.0006$ per side (taker). The practical breakeven R shifts slightly higher.

**Design target:** $R \in [3.0,\ 4.0]$

At $R = 3.0$, $X = €500$:

$$\mathbb{E}[EV] = 500 \cdot [0.425 \cdot 3.0 - 0.575] = 500 \cdot 0.700 = €\mathbf{350\ per\ trade\ gross}$$

This figure is the pre-backtest theoretical ceiling. The actual figure will be lower once slippage, fee drag, and real WR are incorporated.

---

### 1.5 Implications for Strategy Design

The math imposes concrete constraints on every subsequent design decision:

| Parameter | Constraint | Derived from |
|---|---|---|
| Reward:Risk | $R \geq 3.0$ | Integral result at $\bar{w} = 0.425$ |
| Win rate target | $w \in [0.35, 0.50]$ | Breakout sniper prior |
| Entry selectivity | High — few, clean setups | Low WR requires high R to compensate |
| Trade frequency | Low | Selectivity + 4H timeframe, required due to fees |
| Stake | €500 | Fixed capital budget |

---

## Phase 2 — Strategy Design

> **Reference:** `CTAAggressiveBreakout` (Donchian/Chandelier, 5m) used as structural inspiration.
> **Divergences from reference:** Keltner Channels instead of Donchian, fixed TP instead of trailing exit, 4H timeframe, ADX confirmation added.

---

### 2.1 Timeframe

**4H.** Rationale: low trade frequency is a design requirement from Phase 1. Higher timeframes naturally filter noise, reduce fee drag, and produce larger average moves — all consistent with the R ≥ 3.0 constraint. Each candle represents a meaningful price structure rather than microstructure noise.

---

### 2.2 Entry Criteria

A valid long entry requires **all four conditions** to be true simultaneously on candle close:

**Condition 1 — Keltner Channel breakout**
Close price crosses above the upper Keltner Channel band. The channel uses a 20-period EMA as midline with ATR-based width. The upper band is computed on the *previous* candle (`shift(1)`) to prevent lookahead bias.

$$KC_{upper} = EMA_{20} + k \cdot ATR_{10}$$

Default multiplier $k = 2.0$, hyperoptable.

**Condition 2 — ATR expansion**
Current ATR must be above its own N-period moving average, confirming that volatility is expanding rather than contracting at the moment of breakout. A breakout into shrinking volatility is likely a fake.

$$ATR_{14} > SMA(ATR_{14},\ 20)$$

**Condition 3 — Volume spike**
Current candle volume must exceed the rolling volume average by a configurable multiplier. High volume confirms genuine conviction behind the move.

$$Volume > vol\_sma_{20} \times vol\_mult$$

Default $vol\_mult = 1.5$, hyperoptable in range $[1.0,\ 2.5]$.

**Condition 4 — ADX confirmation**
ADX must be above a minimum threshold and rising, confirming that trend strength is building rather than dissipating. This is the regime filter — it prevents entries during ranging, choppy markets where breakouts fail at high rates.

$$ADX_{14} > 20 \quad \text{and} \quad ADX_{14} > ADX_{14}[-1]$$

Threshold hyperoptable in range $[15,\ 30]$.

---

### 2.3 Stop Loss

ATR-based, placed below the breakout candle's low with a multiplier buffer:

$$SL_{price} = entry\_price - atr\_mult \times ATR_{14}$$

Default $atr\_mult = 1.5$, hyperoptable in range $[1.0,\ 2.5]$.

This is the **reference level** for R calculation. The SL distance in price terms defines one unit of R.

Implemented via `custom_stoploss` using `stoploss_from_absolute` — converts the absolute SL price to the relative ratio Freqtrade requires. Hard fallback stoploss of `-0.10` acts as a safety net if the DataProvider is unavailable.

---

### 2.4 Take Profit

**Fixed at exactly 3× the SL distance.** Not trailing. Not dynamic.

$$TP_{price} = entry\_price + 3.0 \times (entry\_price - SL_{price})$$

Implemented via `minimal_roi` with a single entry keyed to the computed TP percentage. This is non-negotiable — a trailing exit changes the effective R on every trade, which invalidates the Phase 1 integral and breaks the mathematical relationship between WR and EV.

The R multiplier of 3.0 is the Phase 1 lower bound. It may be raised during hyperopt if WR validates above 42.5%, but must never fall below 2.5 without re-running the derivation.

---

### 2.5 Regime Filter Summary

| Filter | Purpose | Kills |
|---|---|---|
| ATR expansion | Volatility is growing | Low-volatility fake breakouts |
| Volume spike | Conviction behind move | Thin-volume wicks |
| ADX rising > 20 | Trend is strengthening | Range-bound chop entries |

All three must pass. Any single failure = no trade.

---

### 2.6 What This Strategy Is Not

- **Not a trend follower.** It does not trail stops or let winners run indefinitely. It enters at the breakout and exits at a fixed target.
- **Not mean reversion.** It requires expanding volatility and trend strength, not extremes.
- **Not high frequency.** On 4H with four entry conditions, trade count will be low — this is by design.

---

### 2.7 Parameter Summary

| Parameter | Default | Hyperopt Range | Space |
|---|---|---|---|
| `kc_period` | 20 | 10–40 | buy |
| `kc_mult` | 2.0 | 1.5–3.0 | buy |
| `atr_period` | 14 | 7–21 | buy/sell |
| `atr_mult_sl` | 1.5 | 1.0–2.5 | sell |
| `vol_sma_period` | 20 | 10–40 | buy |
| `vol_mult` | 1.5 | 1.0–2.5 | buy |
| `adx_period` | 14 | 10–20 | buy |
| `adx_threshold` | 20 | 15–30 | buy |
| `rr_ratio` | 3.0 | 2.5–5.0 | sell |

---

## Phase 3 — Backtesting

> *To be completed in Freqtrade.*

The key validation question: does the empirical WR from backtests fall within the assumed range $[0.35, 0.50]$? If not, return to Phase 1, update the prior, and re-derive $R$.

---

