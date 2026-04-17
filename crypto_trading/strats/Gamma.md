# $\Gamma$

## Thesis

**Gamma ($\Gamma$)** is a trading strategy grounded in **actual, concrete, market-agnostic** mathematical models.
Rather than being designed around a specific signal or indicator, Gamma works in reverse: it uses
**integration over uncertainty ranges** to determine what win rate and R:R ratio a strategy *must*
achieve in order to maximise **expected log-wealth growth** — the correct objective for compounding
capital — given a fixed capital base, fee structure, and leverage, while also penalising for
**strategy implementation difficulty**.

> **Clarification:** strategy implementation difficulty is denoted $D_i$. It is a functional measure
> of how sensitive the strategy's expected growth is to mis-estimation of its parameters — not a
> measure of EV itself. A strategy with tight tolerances on $w$ and $r$ (i.e. one that collapses
> badly if your estimates are even slightly wrong) has high $D_i$ and should be penalised
> accordingly. Formal definition in §2.1.

> **Note on optimisation target:** EV maximisation alone is the wrong objective for a repeated-bet
> compounding context — it ignores variance and leads to overbetting and eventual ruin. The correct
> objective is maximising the **Expected Growth Rate** $G$, defined as the expected log-wealth
> increment per trade. Kelly sizing falls out naturally from this. $EV$ is preserved as a diagnostic
> tool, not as the primary optimisation target.

> **Note on mathematical method:** double integration over $(w, r)$ uncertainty ranges is the
> primary tool for computing $E[G]$ and $D_i$.

---

## Development Plan

- **Phase 1:** Strategy theorizing — grounding approach, exchange, constraints
- **Phase 2:** Mathematical model — $G$, $D_i$, double integration, results table
- **Phase 3:** Strategy design — signal logic, indicators, timeframe
- **Phase 4:** Python implementation inside Freqtrade
- **Phase 5:** Automated backtesting framework
- **Phase 6:** Result analysis and iteration

---

## Phase I — Constraints & Ground Rules

Gamma will be deployed on a VPS with starting capital $X = 100,000\$$. The exchange is **Bitget**,
trading **perpetual futures contracts** with leverage $L = 1$. The following rules are
strategy-performance-agnostic — they hold regardless of what signal logic we eventually design:

**Rule 1 — Controlled trade frequency.**
Bitget perpetual futures carry non-trivial fees. At $L = 2$ and limit-order rate $f_r = 0.0004$,
each round-trip costs $0.40 per trade regardless of outcome. Overtrading erodes edge faster than
any signal weakness. Frequency must be governed by the $G > 0$ condition, not by intuition.

**Rule 2 — Limit orders exclusively.**
Limit orders on Bitget are approximately 60% cheaper than market orders. Given that fees are baked
into the mathematical model, using market orders would invalidate our fee assumptions. All entries
and exits must use limit orders. The round-trip fee rate is therefore fixed at $f_r = 0.0004$.

**Rule 3 — Large-move dependency.**
Because frequency is controlled and each trade carries a fixed fee cost, each trade must carry
substantial directional weight. This biases the strategy toward: a) trend following,
b) breakout trading, c) mean reversion, or d) a principled blend. The choice among these will be
made in Phase III, after Phase II establishes the required $(w, r)$ operating window.

> The win rate $w$ is not a single point — it is an interval $[w_\text{low}, w_\text{high}]$
> reflecting genuine uncertainty about forward performance. Any strategy that only works at a single
> precise $w$ value is too fragile to deploy. Robustness across the full interval is a hard
> requirement.

---

## Phase II — Mathematical Model

The objective of Phase II is to produce a rigorous, closed mathematical specification that any
trading algorithm implemented under Gamma must satisfy. The outputs are: a formal $D_i$ definition,
the growth rate function $G(w, r, f)$, its expectation over uncertainty ranges via double
integration, the optimal Kelly fraction $f^*$, and a summary constraints table.

### 2.1 — Quantifying $D_i$

$D_i$ must capture something that $EV$ and $G$ do not — namely, how much the strategy's performance
degrades when our parameter estimates are wrong. A strategy robust to estimation error has low
$D_i$; a fragile one has high $D_i$.

The earlier candidate $D_i = w \cdot r$ is discarded: it is proportional to EV and adds no
independent information.

Instead, we define $D_i$ as a **sensitivity functional** — a first-order measure of how much $G$
varies in response to perturbations in $w$ and $r$:

$$D_i(w, r, f) = \left|\frac{\partial G}{\partial w}\right| \cdot \Delta w + \left|\frac{\partial G}{\partial r}\right| \cdot \Delta r$$

Where $\Delta w$ and $\Delta r$ are the half-widths of the uncertainty intervals:

$$\Delta w = \frac{w_\text{high} - w_\text{low}}{2}, \qquad \Delta r = \frac{r_\text{high} - r_\text{low}}{2}$$

The partial derivatives are evaluated at the interval midpoints $\bar{w}$, $\bar{r}$, and at the
optimal sizing $f^*$. Intuitively: $D_i$ is the expected first-order drop in $G$ if parameter
estimates are off by their typical uncertainty. A low-$D_i$ strategy stays profitable even when you
are wrong about $w$ and $r$.

The partial derivatives are computed explicitly in §2.4 once $G$ is fully defined.

### 2.2 — Why $G$, not $EV$

$EV$ measures the average dollar return per trade. But dollar return is the wrong thing to maximise
when reinvesting and compounding. Consider: a strategy with $EV = +50\$$ but high variance will
destroy a 100,000$ account in a drawdown long before the expectation materialises. The St. Petersburg
paradox formalises exactly this failure.

The correct objective for a sequence of reinvested trades is the **expected logarithmic wealth
increment per trade**, or Expected Growth Rate:

$$G = \mathbb{E}[\log(1 + f \cdot X)]$$

where $f$ is the fraction of capital risked and $X$ is the net return random variable per
unit risked. For a binary win/loss model this becomes:

$$G(w, r, f) = w \cdot \log(1 + f \cdot r_\text{net}) + (1 - w) \cdot \log(1 - f \cdot r_\text{risk})$$

Where the fee-adjusted net returns are:

$$r_\text{net} = r - L \cdot f_r \qquad \text{(reward per unit risked, after fees)}$$

$$r_\text{risk} = r_2 + L \cdot f_r \qquad \text{(risk per unit risked, after fees)}$$

With our fixed parameters $L = 2$, $f_r = 0.0004$, $r_2 = 1$:

$$r_\text{net} = r - 0.0008, \qquad r_\text{risk} = 1.0008$$

$G > 0$ is the fundamental viability condition — a strategy with $G \leq 0$ destroys capital in
expectation on a log scale, regardless of its raw $EV$. Note that $G$ is a log-return; the actual
per-trade growth is $e^G - 1$. For small $G$, the approximation $e^G - 1 \approx G$ holds well,
but they diverge at larger values.

### 2.3 — EV as a Diagnostic (Preserved)

Although $EV$ is no longer the primary optimisation target, it remains a useful sanity check.
The full fee-aware $EV$ model:

$$EV(X) = [w \cdot r \cdot X] - [(1-w) \cdot r_2 \cdot X] - [X \cdot L \cdot (f_\text{entry} + f_\text{exit})]$$

With volatility-anchored reward and risk:

$$r = n \cdot \sigma, \qquad r = m \cdot r_2$$

where $n$ is the noise multiplier ($n = 2$ or $3$ are standard) and $m$ is the desired reward
multiple over risk. This anchors stop and target placement to actual market volatility rather than
arbitrary distances.

The Kelly Criterion gives the optimal fraction of capital to risk per trade:

$$K^* = \frac{w \cdot r - (1 - w) \cdot r_2}{r}$$

$K^*$ is derived by maximising $G$ with respect to $f$ and setting $\partial G / \partial f = 0$.
In the binary model this yields exactly the formula above, confirming internal # Standard 001

**Authors:** Fedor Palko

## Thesis

The Gamma standard allows for easy validation of trading strategies based purely on mathematical calculations and theories. We aim to ground our strategy mathematically and design rules which work market-agnostic and should be a healthy indicator of strategy feasibility. In this document we outline both the standard, and an example strategy that is compliant.

The example strategy is meant for institutions designed to grow capital. Think quant prop firms or retail traders.

## Development Plan

1. Defining the strategy scope, trading style
2. Mathematical analysis
3. Strategy design
4. Strategy implementation
5. Backtests, iteration
6. Conclusion

## 1. Defining the scope

### 1.1. Basic constraints

Before we can design the strategy itself, we need to set some basic information that we will work with:
- The strategy will be backtested and paper traded with a budget of $100,000\$$ on the Binance exchange.
- Our primary goal is to achieve steady growth without low-moderate risk levels.
- Our trading approach will be momentum/trend following on the 4h timeframe.
- We will only trade high-market cap pairs (excl. stable coins like `USDT` or `USDC`)
- Our position sizing will be conservative, with only $1-2\%$ risked per each trade.
- The Binance fee structure for futures and limit orders has been calculated as a single round-trip rate that we account for, set as $f = 0.0004$
- We will not trade with any leverage whatsoever (so 1x)

And then some elementary, pre-phase II mathematical criteria the strategy must pass:
- It must exceed a winrate of $W$
- Its expected growth rate per each trade must be $G > 0$
- Its maximum drawdown must not exceed $D_{max}$
- Its profit factor must be $PF > 1$

The specific values for the variables will be grounded after the in-depth mathematical analysis.

## 2. Mathematical analysis

### 2.1. Methods

In order to find the values of $W, G, D_{max}, PF$ we will utilize:
- Integration to find the value from $W \in [\omega_{min}, \omega_{max}]$. For realistic purposes, we will set $\omega_{min} = 0.35$ and $\omega_{max} = 0.65$ to match standard institutional win rates.
- Integration to find $R_w$ (the reward ratio in the standard R:R), if $R_w \in [\rho_{min}, \rho_{max}]$. We will set $\rho_{min} = 1$ and $\rho_{max} = 3$ to match conventional R:R ratios.
- Integration to find $D_{max}$ (the maximum drawdown), if $D_{max} \in [\delta_{min}, \delta_{max}]$

Our main rule is simple: **finding the maximum amount of $G$ possible thanks to integrals**. 

### 2.2. Function

Let's define $G$ as a function of $W$, $f$, $r$ (the position size as a decimal) and $R_w$: 

$\boxed{G(W,Rw​,r,f)=W⋅ln[(1+r⋅Rw​)(1−f)]+(1−W)⋅ln[(1−r−f(2−r))]}​$

This is going to be our main function we will use in integration.

### 2.3. Boundary analysis

We fix $r = 0.01$ (conservative end of our 1–2% range) and $f = 0.0004$. Setting $G = 0$ and solving for $W$ gives the minimum viable win rate as a function of $R_w$:

$$W^*(R_w) = \frac{-\ln(1 - r - f(2-r))}{\ln\!\big((1+r \cdot R_w)(1-f)\big) - \ln(1 - r - f(2-r))}$$

This is the **survival boundary** — any $(W, R_w)$ pair above this curve satisfies $G > 0$. Key observations from the boundary:

- At $R_w = 1.0$ (1:1 R:R), you need roughly $W \geq 50.2\%$ just to survive fees
- At $R_w = 2.0$, the floor drops to ~W ≥ 34%, comfortably inside your [0.35, 0.65] range
- At R_w = 3.0, even W ≈ 26% would technically be viable — well below our ω_min

The slider lets you see how tightening r to 2% affects the picture — the boundary barely shifts, confirming position sizing has minimal impact on viability at these levels. The dominant factor is R_w.

**Conclusion for the standard:** any compliant strategy must target $R_w \geq 1.5$ as a hard minimum, which makes the $W$ requirement comfortably achievable within realistic institutional ranges.

consistency between
§2.2 and §2.3.

> **Practical note:** raw Kelly is aggressive and produces large drawdowns. Gamma uses
> **half-Kelly** by default: $f = \frac{1}{2} K^*$. This reduces variance at the cost of
> slightly slower growth.

### 2.4 — Double Integration over $(w, r)$ Uncertainty

In practice, $w$ and $r$ are never known exactly. Estimates from backtests give us intervals.
Rather than optimising at a point, we optimise $E[G]$ over those intervals, treating
$w$ and $r$ as uniformly distributed on $[w_\text{low}, w_\text{high}]$ and
$[r_\text{low}, r_\text{high}]$ respectively.

The expected growth rate under parameter uncertainty is:

$$\mathbb{E}[G](f) = \frac{1}{\Delta W \cdot \Delta R} \int_{w_\text{low}}^{w_\text{high}} \int_{r_\text{low}}^{r_\text{high}} G(w, r, f) \, dr \, dw$$

where $\Delta W = w_\text{high} - w_\text{low}$ and $\Delta R = r_\text{high} - r_\text{low}$.

Since $w$ appears linearly in $G$, the double integral separates. Defining $\bar{w} = (w_\text{low} + w_\text{high}) / 2$, the integral over $w$ reduces trivially:

$$\mathbb{E}[G](f) = \frac{1}{\Delta R} \int_{r_\text{low}}^{r_\text{high}} \left[ \bar{w} \cdot \log(1 + f(r - Lf_r)) + (1 - \bar{w}) \cdot \log(1 - f \cdot r_\text{risk}) \right] dr$$

The second log term is constant in $r$ (since $r_2$ is fixed), so:

$$\mathbb{E}[G](f) = \frac{\bar{w}}{\Delta R} \int_{r_\text{low}}^{r_\text{high}} \log(1 + f(r - Lf_r)) \, dr + (1 - \bar{w}) \cdot \log(1 - f \cdot r_\text{risk})$$

The remaining integral resolves via the closed form:

$$\int \log(1 + ar) \, dr = \frac{(1 + ar)\log(1 + ar) - (1 + ar)}{a} + C$$

This gives a fully closed expression for $E[G](f)$. The optimal sizing $f^*$ is found
numerically by evaluating $E[G](f)$ on a fine grid over $f \in (0, 1)$ and taking
the argmax.

**Partial derivatives of $G$, evaluated at $(\bar{w}, \bar{r}, f^*)$:**

$$\frac{\partial G}{\partial w} = \log(1 + f \cdot r_\text{net}) - \log(1 - f \cdot r_\text{risk})$$

$$\frac{\partial G}{\partial r} = \frac{w \cdot f}{1 + f \cdot r_\text{net}}$$

Therefore the explicit $D_i$ formula is:

$$D_i = \left[\log(1 + f^* r_\text{net}) - \log(1 - f^* r_\text{risk})\right] \cdot \Delta w + \frac{\bar{w} \cdot f^*}{1 + f^* r_\text{net}} \cdot \Delta r$$

A strategy is **robust** if $D_i < 0.25 \cdot G(\bar{w}, \bar{r}, f^*)$ — i.e. first-order
degradation under typical estimation error is less than 25% of nominal growth.

### 2.5 — Results & Constraints Table

Computed with $L = 2$, $f_r = 0.0004$, $r_2 = 1$, half-Kelly sizing.

Minimum win rate required for $G > 0$ at each reward ratio:

| $r$ | $w_\text{min}$ | $G$ per trade at $w=0.55$ | Actual growth $e^G - 1$ |
|:---:|:---:|:---:|:---:|
| 1.5 | 0.401 | 0.0503 | 5.16% |
| 2.0 | 0.334 | 0.0749 | 7.77% |
| 2.5 | 0.287 | 0.0938 | 9.83% |
| 3.0 | 0.251 | 0.1087 | 11.48% |

Fee cost at $X = 500$ $, $L = 2$:

| Trades/day | Daily fee | % of capital |
|:---:|:---:|:---:|
| 1 | $0.40 | 0.08% |
| 5 | $2.00 | 0.40% |
| 10 | $4.00 | 0.80% |
| 20 | $8.00 | 1.60% |

Any Gamma-compliant algorithm must satisfy:

| Parameter | Constraint | Rationale |
|:---|:---:|:---|
| $G(\bar{w}, \bar{r}, f^*)$ | $> 0$ | Non-negotiable viability condition |
| $E[G](f^*)$ | $> 0$ over full range | Robust profitability under uncertainty |
| $w_\text{low}$ | $\geq 0.40$ | Minimum floor for $G > 0$ at $r \geq 1.5$ |
| $r_\text{low}$ | $\geq 1.5$ | Below this, required $w$ is unrealistically high |
| Position sizing | $f = \frac{1}{2} K^*$ | Half-Kelly enforced to limit drawdown |
| $D_i$ | $< 0.25 \cdot G(\bar{w}, \bar{r}, f^*)$ | Robustness tolerance |
| Trade frequency | $\leq 10$/day | Beyond this, fees exceed 0.80%/day of capital |
| Order type | Limit only | $f_r = 0.0004$ assumption requires this |
| Leverage | $L = 2$ | Fixed; changing this invalidates all values above |

### 2.6 — Conclusion

Phase II establishes that Gamma's optimisation target is the **Expected Growth Rate** $G$, not raw
$EV$. The double integral over $(w, r)$ uncertainty intervals gives a fee-aware, leverage-aware,
volatility-anchored expected growth function whose maximum defines both the optimal Kelly fraction
$f^*$ and — through its partial derivatives — the robustness measure $D_i$.

Any strategy entering Phase III must credibly achieve a $(w_\text{low}, w_\text{high}, r_\text{low}, r_\text{high})$ operating window satisfying all constraints in §2.5. Signal logic, indicator
choice, and entry conditions are all subordinate to these requirements.

---

## Phase III — Strategy Design

### 3.1 — Regime Selection

Phase II fixes the required operating window: $w \geq 0.40$, $r \geq 1.5$, at most 10 trades/day.
The question for Phase III is: which market regime consistently delivers this on perpetual futures?

Three candidate approaches evaluated against Phase II constraints:

**Trend following.** Historically produces lower $w$ (40–55%) with higher $r$ (2.0–4.0+) due to
letting winners run. Naturally compatible with low frequency — trades are infrequent by design.
Vulnerable to choppy/ranging markets; requires a regime filter to avoid entering sideways
conditions.

**Breakout trading.** Can produce moderate $w$ (45–60%) with moderate $r$ (1.5–2.5). The primary
risk is false breakouts devastating $w$ without a confirmation mechanism. Viable as an entry
trigger within a confirmed trend, not as a standalone approach.

**Mean reversion.** Typically produces higher $w$ (55–70%) but lower $r$ (1.0–1.5), frequently
below the $r_\text{low} \geq 1.5$ floor. Does not fit Phase II constraints as a primary approach.

**Verdict:** trend following with a regime filter is the primary approach. Its $(w, r)$ profile is
historically compatible with the Phase II window. Breakout logic is incorporated as the entry
trigger within a confirmed trend.

### 3.2 — Timeframe Stack and Candle Type

Timeframe selection determines trade frequency and therefore daily fee exposure. The target of
$\leq 10$ trades/day with large per-trade moves points to a multi-timeframe structure:

- **1D real candles** — trend direction and regime confirmation only, no entries
- **4H Heikin-Ashi candles** — trend strength and pullback detection
- **4H real candles** — entry quality filter, stop and target placement, ATR regime check

Heikin-Ashi (HA) candles smooth price action by averaging open and close across candles, reducing
false signals in ranging conditions and making pullbacks to trend indicators cleaner and more
reliable. However, HA prices are synthetic — they do not correspond to any real price that traded.
Using them for execution would cause stop and target placements to diverge from backtested values,
invalidating the $r$ assumptions in the Phase II model.

The solution is a strict two-layer separation: HA candles are used exclusively for signal
generation (trend detection, pullback identification, ADX reading), while all execution logic —
entry price, stop loss, take profit, ATR sizing — is computed on real candles only. This captures
the smoothing benefit of HA without contaminating the fee-adjusted $r_\text{net}$ and
$r_\text{risk}$ values that $G$ depends on.

In Freqtrade, this is implemented by generating a separate HA dataframe inside
`populate_indicators()` and merging the HA-derived indicator columns back into the main real-candle
dataframe for signal evaluation.

### 3.3 — Indicators

Each indicator serves exactly one of three roles: regime confirmation, entry trigger, or volatility
sizing. No indicator is included for signal volume.

**Regime confirmation (1D real candles):**
EMA 200 and EMA 50. Price above EMA 200 defines a bullish regime; below defines bearish. EMA 50
above EMA 200 provides secondary trend alignment confirmation. Only longs are taken in bullish
regime, only shorts in bearish.

**Entry trigger (4H HA candles):**
EMA 21 for pullback detection. In a trending regime, a HA close back above EMA 21 after a pullback
is the entry signal — confirmation is required, not just a touch, which eliminates entries into
price grinding through the EMA. ADX(14) gates trend strength: only enter when ADX > 20, filtering
out sideways conditions where the EMA 200 regime filter alone is insufficient.

**Entry quality and volatility sizing (4H real candles):**
RSI(14) confirms the entry is not overextended — valid range is 35–60 for longs, 40–65 for shorts.
ATR(14) anchors stop and target placement per $r = n \cdot \sigma$, and provides the ATR regime
check described in §3.4.

| Indicator | Candle type | Timeframe | Role |
|:---|:---:|:---:|:---|
| EMA 200 | Real | 1D | Regime filter — direction only |
| EMA 50 | Real | 1D | Secondary trend confirmation |
| EMA 21 | Heikin-Ashi | 4H | Pullback entry trigger |
| ADX(14) | Heikin-Ashi | 4H | Trend strength gate |
| RSI(14) | Real | 4H | Entry quality filter |
| ATR(14) | Real | 4H | Volatility sizing and regime check |

### 3.4 — Entry & Exit Logic

**Long entry — all five conditions must be satisfied simultaneously:**

1. Price > EMA 200 on 1D real, and EMA 50 > EMA 200 on 1D real (bullish regime)
2. ADX(14) > 20 on 4H HA (trend is strong enough to trade)
3. HA close crossed back above EMA 21 on 4H HA after a pullback (confirmation, not touch)
4. RSI(14) between 35 and 60 on 4H real (entry not overextended)
5. Current ATR(14) < $1.5 \times$ ATR 50-period average on 4H real (normal volatility regime)

**Short entry:** conditions 2–5 mirrored, with condition 1 requiring price < EMA 200 and EMA 50 <
EMA 200 on 1D real.

**Entry order:** limit order placed at the 4H real candle close price at signal confirmation.

**Stop loss:** entry price minus $1 \times$ ATR(14) on 4H real, placed as limit order.

**Take profit:** entry price plus $2 \times$ ATR(14) on 4H real, placed as limit order.
Baseline $r = 2.0$, satisfying $r_\text{low} \geq 1.5$ with margin.

**Position sizing:** dynamic half-Kelly via Freqtrade's `custom_stake_amount()` callback.
At each entry, $K^*$ is computed from $\bar{w}$ and $\bar{r}$ derived from the last 30 closed
trades in history, and the stake returned is $f = \frac{1}{2} K^*$ of available capital.
When fewer than 30 closed trades exist (early deployment), a conservative fallback of $f = 0.10$
is used. Config requires `stake_amount = "unlimited"` and `max_open_trades = 1`.

### 3.5 — Robustness Filters: Theoretical Basis

The three filters in §3.4 (ADX gate, ATR regime check, HA candle confirmation) are not arbitrary
additions — each addresses a specific failure mode identified during Phase III analysis that would
cause $w$ to fall below the $w_\text{low} \geq 0.40$ floor without triggering the 1D regime
filter.

**Ranging within a trend (ADX gate).** BTC frequently consolidates at the 4H level while remaining
above EMA 200 on 1D — the regime filter never triggers, but EMA 21 pullback signals fire
repeatedly into sideways chop. ADX < 20 identifies this condition and suppresses entries. Expected
effect: reduces signal frequency, increases $w$ by eliminating low-quality setups.

**Abnormal volatility (ATR regime check).** During liquidation cascades or macro events, ATR can
double overnight. Stops widen disproportionately, position size shrinks via Kelly, and the absolute
target becomes difficult to reach before retracement. Capping at $1.5 \times$ the 50-period ATR
average skips entries where the $r = 2.0$ assumption is structurally compromised. Expected effect:
protects $r_\text{net}$ stability across deployment.

**EMA grinding (HA confirmation).** In weak trends, price crosses EMA 21 repeatedly without
committing — entering on touch produces a string of small losses that devastate $w$. Requiring a
HA close back above EMA 21 adds one candle of confirmation lag but eliminates the majority of
these entries. Expected effect: raises $w_\text{low}$ by approximately 5–8 percentage points based
on analogous EMA pullback system behaviour.

### 3.6 — Pair Selection

Gamma is deployed across a fixed pairlist of perpetual futures on Bitget. Pair inclusion requires
satisfying three criteria simultaneously:

**Liquidity floor.** Minimum $500M USDT daily volume on Bitget perpetuals. Required for limit
order fill reliability at $L = 2$ — below this threshold, slippage on limit fills begins to
meaningfully erode $r_\text{net}$.

**Trend persistence.** Hurst exponent $H > 0.5$ over a multi-year lookback. $H > 0.5$ indicates
positive return autocorrelation — the asset trends rather than mean-reverts at the relevant
timescales. This is a quantitative requirement, not an aesthetic one, and should be verified per
pair before live deployment.

**ADX trending frequency.** More than 40% of historical 4H candles with ADX(14) > 20. Pairs
spending the majority of their time ranging are structurally incompatible with the signal logic
regardless of their liquidity or Hurst exponent.

Approved pairlist:

| Pair | Rationale |
|:---|:---|
| BTC/USDT | Deepest liquidity, benchmark trend asset, most backtesting data available |
| ETH/USDT | Second deepest liquidity, strong trend persistence, high ADX frequency |
| SOL/USDT | Strong directional moves, sufficient liquidity, passes Hurst criterion |
| BNB/USDT | Consistent liquidity, moderate trend persistence |
| LINK/USDT | Historically clean trend structure, strong directional moves — provisional pending ADX frequency verification |

BTC/USDT is the primary pair for Phase IV implementation and initial backtesting. Remaining pairs
are added sequentially in Phase VI after BTC results establish a baseline.

---

*Phase IV — Python implementation inside Freqtrade: pending.*