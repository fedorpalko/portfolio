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

*pending*