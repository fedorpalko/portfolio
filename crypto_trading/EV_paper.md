## Thesis

In this paper I hope to explore and build upon a standalone and simple EV per trade formula, where I eventually hope to define $G$ as the standard ultimate universal growth rate model - basically the % of which your stake will grow each trade. $G$ accounts for compounding, fee drag, volatility and win rate uncertainty. I want to do it in a way where it is both simple enough to be understood by anyone and yet complex enough to be statistically sound and useful for actual trading strategies, including my own.

## Sections

1. [EV Uniform Model](#1-ev-uniform-model)
2. [EV Uniform Model (Fees and Commission)](#2-ev-uniform-model-fees-and-commission)
3. [EV Volatile Model](#3-ev-volatile-model)
4. [EV Volatile Model (Uncertain Winrate)](#4-ev-volatile-model-uncertain-winrate)
5. [Universal Growth Rate Model](#5-universal-growth-rate-model)
6. [Conclusion](#6-conclusion)

## 1. EV Uniform Model

### Thesis

We start out with a plain EV Uniform Model which is used to return the expected profit per each trade in plain $ or whatever currency you want to choose.
It stems from the simple definition of expected value for trades: expected value is the sum of all possible outcomes multiplied by their probabilities.

Now let's define some variables:
- $\omega$ - represents the probability of winning a trade
- $\bar{R}$ - represents the reward value in a fixed RR ratio (example: RR is 1:1.5, so $\bar{R} = 1.5$)
- $S$ represents the stake for a trade, e.g. the position size in real currency
- $L$ represents the leverage to amplify your position size, as a natural number
- $\rho$ represents our expected value per trade

### Definition

And now we can define the formula for $\rho$:

$$\boxed{\rho = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L)}$$

This formula is intuitive, but it fails to account for fees or volatility. It can be applied in backtests for a rough estimate, assuming you already have your win rate defined and all information - you just want the EV assuming you went exactly like this.

### Example

Let's say we have a strategy that we backtested and it gave us the following results:
- Win rate: 60%
- Reward:Risk Ratio (RR): 1:2
- We take $50 as our stake
- We use 2x leverage

Now, let's calculate the EV using our formula:

$$\rho = (0.60 \cdot \$50 \cdot 2 \cdot 2) - ((1 - 0.60) \cdot \$50 \cdot 2)$$
$$\rho = (0.60 \cdot \$200) - (0.40 \cdot \$100)$$
$$\rho = \$120 - \$40$$
$$\rho = \$80$$

This means that, on average, we can expect to make $80 per each trade with this strategy. While we might be celebrating this glorious victory, any strategy that seems robust on paper can fail easily, because the market is non-linear.

## 2. EV Uniform Model (Fees and Commission)

### Thesis

We do already have $\rho$ defined, which can help us a ton here. In this section we will introduce fees and commissions into our EV calculations. Let's first take a look at our original formula:

$$\boxed{\rho = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L)}$$

### Definition

If we wanted to include fees, we would need to define $f$, which is going to be a variable that represents how much real currency we lose per trade due to commission rates. 

$$\boxed{f = (f_e + f_x) \cdot S}$$

In here, $f_e$ is the exchange entry fee rate represented as a decimal, $f_x$ is the exchange exit fee rate represented as a decimal, and $S$ is our stake.

Combinining both of these, we can derive our final EV Uniform Model (UM):

$$\boxed{UM = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - f}$$

Or expanded:

$$\boxed{UM = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L}$$

We have successfully expanded the original model, and now we added fees and commissions into our calculations. Now we can assume that this model returns more accurate results, but it's still basically just the original uniform model, although now with more realism.

### Example

Let's say we have a strategy that we backtested and it gave us the following results:
- Win rate: 60%
- Reward:Risk Ratio (RR): 1:2
- We take $50 as our stake
- We use 2x leverage
- Exchange fees are 0.2% for entry and 0.2% for exit

Now, let's calculate the expected value of $\rho$ using our formula:

$$\rho = (0.60 \cdot \$50 \cdot 2 \cdot 2) - ((1 - 0.60) \cdot \$50 \cdot 2) - (0.002 + 0.002) \cdot \$50$$
$$\rho = (0.60 \cdot \$200) - (0.40 \cdot \$100) - (0.004) \cdot \$50 \cdot 2$$
$$\rho = \$120 - \$40 - \$0.4$$
$$\rho = \$80 - \$0.4$$
$$\rho = \$79.6$$

Compared to our initial UM result, we have achieved a result that while only $\$0,4$ smaller, imagine what this could do at a strategy trading with $\$50,000,000$. The fee would be $\$400,000$. Astronomical. Further sections will further demonstrate how to rigorously account for fees and fee drag.

## 3. EV Volatile Model

### Thesis

The real market is not linear. Even with a well-backtested strategy, individual trade outcomes will deviate from the expected value $\rho$ due to volatility — early exits, slippage, sudden market shifts, and noise. The EV Uniform Model assumes every winning trade returns exactly $S \cdot L \cdot \bar{R}$ and every losing trade loses exactly $S \cdot L$. This is a useful abstraction, but it is not reality.

This section introduces $\sigma$, the standard deviation of per-trade P&L outcomes derived from backtest data, as a measure of that deviation. Critically, volatility is not neutral — while $\varepsilon$ is symmetric around zero by definition, negative deviations compound asymmetrically and erode capital faster than equivalent positive deviations recover it. The resulting model treats each trade's P&L as a random variable rather than a fixed outcome, making this the first section to require real backtest data rather than assumed parameters (but don't worry - you can easily derive it after your backtest!).

Therefore, we return something that works across multiple trades, and it's a better indicator of strategy power.

### Variables

Building on all variables from Sections 1 and 2, we introduce:

- $\sigma$ — the standard deviation of per-trade P&L outcomes, derived from backtest data
- $\varepsilon$ — a random perturbation per trade, drawn from a normal distribution with mean $0$ and variance $\sigma^2$, basically just random noise around $\rho$
- $\tilde{\rho}$ — the volatile expected value per trade (a random variable drawn from a distribution)
- $n$ — the number of trades in the backtest sample
- $r_i$ — the P&L of the $i$-th trade in the backtest

### Derivation of $\sigma$

We want to quantify how much individual trade outcomes scatter around the mean P&L $\bar{r}$. The natural measure of scatter is **variance** — the average squared deviation from the mean across all trades in our backtest sample:

$$\text{Var} = \frac{1}{n-1}\sum_{i=1}^{n}(r_i - \bar{r})^2$$

Note that we divide by $n-1$ rather than $n$. This is known as **Bessel's correction** — when estimating variance from a sample rather than a full population, dividing by $n-1$ produces an unbiased estimate. Dividing by $n$ would systematically underestimate the true variance.

Since variance is expressed in squared currency units, it is not directly interpretable. Taking the square root returns us to the original units:

$$\boxed{\sigma = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n}(r_i - \bar{r})^2}}$$

This is the standard sample standard deviation — a well-established statistical measure. A larger $\sigma$ indicates a more chaotic strategy with wider outcome swings; a smaller $\sigma$ indicates tighter, more predictable trade results.

### Definition

We define the random perturbation $\varepsilon$ as a value drawn from a normal distribution — a symmetric bell curve — centered at zero with spread determined by $\sigma$:

$$\varepsilon \sim \mathcal{N}(0, \sigma^2)$$

The notation $\mathcal{N}(\mu, \sigma^2)$ denotes a normal distribution with mean $\mu$ and variance $\sigma^2$. Here, mean zero means we assume no systematic directional bias — only random noise around the expected outcome. Positive $\varepsilon$ means a trade outperformed $\rho$; negative $\varepsilon$ means it underperformed.

The volatile expected value per trade is then:

$$\boxed{\tilde{\rho} = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L + \varepsilon}$$

It follows that $\mathbb{E}[\tilde{\rho}] = \rho$ — on average, the volatile model returns the same result as Section 2. However, any individual trade can deviate significantly in either direction. A sufficiently negative $\varepsilon$ can turn a theoretically profitable trade into a loss, and across many compounded trades, this variance accumulates into meaningful capital erosion — even when $\rho > 0$.

### Example

Using the same parameters as before:
- Win rate: 60%
- RR: 1:2
- Stake: $50
- Leverage: 2x
- Fees: 0.2% entry, 0.2% exit
- Backtest $\sigma$: $15 (estimated from trade history)

We already know $\rho = \$79.92$ from Section 2. Now, a single trade might realistically return:

$$\tilde{\rho} = \$79.92 + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0, 15^2)$$

So any individual trade could land well above or well below $\rho$. A run of trades with negative $\varepsilon$ can produce a drawdown despite the strategy being profitable in expectation. This is precisely why $\rho$ alone is an insufficient measure of strategy quality — and why Section 5 will introduce $G$, a growth rate that penalises strategies for their volatility, not just their average return.

As we can see, $\tilde{\rho}$ is not a fixed number, but a random variable and more importantly, a random distribution. It's a different level from sections 1 and 2, where we worked with discrete math. We will require this to actually define $G$.

## 4. EV Volatile Model (Uncertain Win Rate)

### Thesis

The volatile model in Section 3 introduced $\varepsilon$ to account for the fact that individual trade outcomes deviate from $\rho$ due to market noise. However, it still treats $\omega$ — the win rate — as a fixed, known quantity. In practice, $\omega$ is itself an estimate derived from a finite backtest sample. A strategy backtested over 20 trades gives a far less reliable win rate estimate than one backtested over 2000 trades, yet the Section 3 model treats both identically.

This section addresses that by modelling $\omega$ as a normally distributed random variable rather than a fixed input. The result is a model with two stacked sources of uncertainty: noisy trade outcomes ($\varepsilon$) and a noisy win rate ($\omega$). Like Section 3, this model is intentionally incomplete — it does not yet penalise the strategy for these compounded uncertainties. That is the role of $G$ in Section 5.

### Variables

Building on all variables from Sections 1–3, we introduce:

- $\bar{\omega}$ — the mean win rate, estimated as the plain average from backtest data
- $\sigma_\omega$ — the standard deviation of the win rate estimate, derived from backtest sample size
- $\omega$ — win rate, now treated as a random variable drawn from $\mathcal{N}(\bar{\omega}, \sigma_\omega^2)$

### Derivation of $\bar{\omega}$

$\bar{\omega}$ is simply the proportion of winning trades in the backtest sample. If the backtest contains $n$ trades of which $n_w$ were winners:

$$\boxed{\bar{\omega} = \frac{n_w}{n}}$$

This is the same $\omega$ used in Sections 1–3, now explicitly defined as a sample estimate rather than a known constant.

### Derivation of $\sigma_\omega$

We model each trade as an independent Bernoulli trial — it either wins with probability $\bar{\omega}$ or loses with probability $1 - \bar{\omega}$. This is consistent with the assumption already embedded in Section 1.

For a proportion estimated from $n$ independent Bernoulli trials, the standard error of that estimate is a well-established statistical result:

$$\boxed{\sigma_\omega = \sqrt{\frac{\bar{\omega}(1 - \bar{\omega})}{n}}}$$

This formula captures the intuitive relationship between sample size and confidence: a larger backtest produces a smaller $\sigma_\omega$, meaning the win rate estimate is more trustworthy. A smaller backtest produces a larger $\sigma_\omega$, meaning the true win rate could plausibly differ significantly from $\bar{\omega}$.

Note that $\sigma_\omega$ is fully determined by $\bar{\omega}$ and $n$ — both of which are already available from backtest data. No additional inputs are required.

### Definition

Win rate is now modelled as a random variable:

$$\omega \sim \mathcal{N}(\bar{\omega}, \sigma_\omega^2)$$

The notation $\mathcal{N}(\mu, \sigma^2)$ denotes a normal distribution with mean $\mu$ and variance $\sigma^2$ — the same bell curve introduced in Section 3. Here, the distribution is centered at $\bar{\omega}$ with spread determined by $\sigma_\omega$. Win rates far from $\bar{\omega}$ are possible but increasingly unlikely.

Substituting this into the volatile model from Section 3, the full uncertain volatile expected value per trade is:

$$\boxed{\tilde{\rho} = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L + \varepsilon}$$

Where both $\omega \sim \mathcal{N}(\bar{\omega}, \sigma_\omega^2)$ and $\varepsilon \sim \mathcal{N}(0, \sigma^2)$ are now random. The formula is structurally identical to Section 3 — the only change is that $\omega$ is no longer a fixed number.

It follows that $\mathbb{E}[\tilde{\rho}] = \rho$ still holds, since $\mathbb{E}[\omega] = \bar{\omega}$ and $\mathbb{E}[\varepsilon] = 0$. However, the variance of $\tilde{\rho}$ is now larger than in Section 3, because uncertainty in $\omega$ adds a second layer of spread on top of $\varepsilon$.

### Example

Using the same parameters as before, now with a small backtest:
- $\bar{\omega} = 0.60$, $n = 30$ trades
- RR: 1:2, Stake: $50, Leverage: 2x
- Fees: 0.2% entry, 0.2% exit
- Backtest $\sigma$: $15

First, we derive $\sigma_\omega$:

$$\sigma_\omega = \sqrt{\frac{0.60 \cdot 0.40}{30}} = \sqrt{\frac{0.24}{30}} = \sqrt{0.008} \approx 0.0894$$

So the true win rate could realistically fall anywhere from ~$42\%$ to ~$78\%$ within two standard deviations of $\bar{\omega}$. For a strategy whose profitability depends on maintaining a 60\% win rate, this is a significant uncertainty — and one that a 30-trade backtest simply cannot resolve.

Compare this to a 1000-trade backtest:

$$\sigma_\omega = \sqrt{\frac{0.60 \cdot 0.40}{1000}} = \sqrt{0.00024} \approx 0.0155$$

Now the win rate is reliably within ~$57\%$ to ~$63\%$ — a much tighter and more trustworthy estimate. This illustrates why backtest sample size is not just a technicality but a core input to strategy evaluation, and why Section 5's $G$ must account for it.

## 5. Universal Growth Rate Model

### Thesis

Sections 1 through 4 each built one layer of realism onto the original EV formula. Section 1 established the base expected profit per trade $\rho$. Section 2 introduced fee drag. Section 3 introduced volatility via $\sigma$. Section 4 introduced win rate uncertainty via $\sigma_\omega$. Each model was intentionally left incomplete — a stepping stone rather than a destination.

This section is the destination.

$G$ is the Universal Growth Rate — the average percentage by which your capital grows per trade, accounting for edge, fees, volatility drag, and win rate uncertainty simultaneously. It is the single number that determines whether a strategy is worth running. $G > 0$ means your capital grows. $G < 0$ means your capital erodes, even if $\rho > 0$. $G = 0$ means you are breaking even after every source of drag has been accounted for.

This is also the first section to operate in a different mathematical space than S1–S4. Prior sections returned results in raw currency — expected profit in dollars. $G$ is a rate, and rates require a capital baseline to normalise against. This necessitates the introduction of a new variable $C$, defined fresh here rather than retrofitted into earlier sections, because S1–S4 did not require it. The distinction is intentional and clean.

### Variables

Building on all variables from Sections 1–4, we introduce one new variable:

- $C$ — total trading capital in currency. This is your full account size, not the amount deployed per trade.

We also redefine $S$ in the context of $G$:

- $S$ — position size as a decimal fraction of $C$, where $S \in (0, 1)$. For example, $S = 0.10$ means 10% of capital is deployed per trade. The actual currency amount deployed is therefore $S \cdot C$.

This redefinition does not contradict S1–S4, where $S$ was treated as a raw currency amount for simplicity. In those sections, $S$ was a concrete dollar figure because the output was also in dollars. Here, $S$ becomes a fraction because the output is a rate. Both usages are consistent within their respective mathematical contexts.

### Derivation of G

$G$ is constructed from three components, each representing a distinct force acting on your capital.

**Component 1 — Base growth rate**

The first component is simply your expected profit per trade $\rho$ from Section 2, normalised by total capital $C$:

$$G_1 = \frac{\rho}{C} = \frac{(\omega \cdot S \cdot C \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot C \cdot L) - (f_e + f_x) \cdot S \cdot C \cdot L}{C}$$

This is the raw edge of your strategy as a fraction of capital. Note that fees are already embedded here as the third term in the numerator — they reduce $G_1$ directly. A strategy must generate enough edge to clear fees before $G_1$ is even positive.

This component is the special case of $G$ when $\sigma = 0$ and $\sigma_\omega = 0$ — perfect certainty, no volatility. In that idealized world, $G = G_1 = \frac{\rho}{C}$.

**Component 2 — Volatility drag**

The second component penalises $G$ for the variance of per-trade outcomes. As established in Section 3, compounding is multiplicative — a 50% loss requires a 100% gain to recover. Volatility therefore destroys geometric growth even when arithmetic EV is positive.

The penalty is derived from log-normal growth theory, where the geometric mean return is approximated as the arithmetic mean minus half the variance, normalised by capital squared:

$$G_2 = -\frac{\sigma^2}{2C^2}$$

A larger $\sigma$ — a more chaotic strategy — incurs a larger penalty. This term is always negative or zero, never positive. It is a pure cost.

**Component 3 — Win rate uncertainty drag**

The third component penalises $G$ for uncertainty in the win rate estimate $\bar{\omega}$. As established in Section 4, $\sigma_\omega$ measures how much the true win rate could plausibly deviate from the backtested estimate. This uncertainty propagates into $\rho$ because $\omega$ directly determines the balance between winning and losing trades.

The sensitivity of $\rho$ to changes in $\omega$ is the total P&L swing per trade — the amount gained on a win plus the amount lost on a loss:

$$\Delta = S \cdot C \cdot L \cdot (\bar{R} + 1)$$

Here $\bar{R}$ is the reward multiplier on a win and $1$ represents the full loss of the deployed amount on a loss. The larger this swing, the more damaging win rate uncertainty becomes. The penalty is:

$$G_3 = -\frac{\sigma_\omega^2 \cdot (S \cdot C \cdot L \cdot (\bar{R} + 1))^2}{2C^2}$$

Like $G_2$, this term is always negative or zero. It is also a pure cost.

### Definition

Combining all three components, the Universal Growth Rate is:

$$\boxed{G = \frac{(\omega \cdot S \cdot C \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot C \cdot L) - (f_e + f_x) \cdot S \cdot C \cdot L}{C} - \frac{\sigma^2}{2C^2} - \frac{\sigma_\omega^2 \cdot (S \cdot C \cdot L \cdot (\bar{R} + 1))^2}{2C^2}}$$

This formula is intentionally left unsimplified so that each term remains directly traceable to its origin in S1–S4, and so that it can be implemented directly in code by substituting values left to right.

$G$ is expressed as a decimal. A result of $0.03$ means your capital grows by approximately 3% per trade on average. A result of $-0.01$ means your capital erodes by approximately 1% per trade on average, compounded.

### How to Use G

$G$ is a strategy feasibility metric, not a prediction. It does not tell you what will happen on any individual trade — $\tilde{\rho}$ from Section 4 handles that. It tells you the long-run trajectory of your capital if you run this strategy repeatedly.

**The threshold that matters is $G = 0$:**

- $G > 0$ — the strategy is feasible. Your capital grows on average per trade after accounting for all costs and uncertainties. A higher $G$ indicates a stronger, more robust strategy.
- $G = 0$ — the strategy is breakeven. Your edge is exactly cancelled by fees, volatility drag, and win rate uncertainty drag combined. Not worth running.
- $G < 0$ — the strategy is not feasible. Your capital erodes over time. Critically, this can occur even when $\rho > 0$ — a strategy with positive expected profit per trade can still destroy capital if volatility or win rate uncertainty is large enough relative to the edge.

This last case is the most important insight of the paper. A positive $\rho$ is a necessary but not sufficient condition for a viable strategy. $G > 0$ is the sufficient condition.

**Practical usage:**

1. Run a backtest and extract $\bar{\omega}$, $n$, $\sigma$, $\bar{R}$, $S$, $L$, $f_e$, $f_x$
2. Define your total capital $C$
3. Derive $\sigma_\omega = \sqrt{\frac{\bar{\omega}(1-\bar{\omega})}{n}}$
4. Plug all values into $G$
5. If $G > 0$, the strategy clears the feasibility threshold. If $G \leq 0$, revise the strategy parameters or collect more backtest data to tighten $\sigma_\omega$

### Example

Using consistent parameters throughout:
- $\bar{\omega} = 0.60$, $n = 30$ trades
- $\bar{R} = 2$, $S = 0.10$, $C = \$1000$, $L = 2$
- $f_e = 0.002$, $f_x = 0.002$
- Backtest $\sigma = \$15$

First, derive $\sigma_\omega$:

$$\sigma_\omega = \sqrt{\frac{0.60 \cdot 0.40}{30}} \approx 0.0894$$

Now compute each component:

$$G_1 = \frac{(0.60 \cdot 0.10 \cdot 1000 \cdot 2 \cdot 2) - (0.40 \cdot 0.10 \cdot 1000 \cdot 2) - (0.004 \cdot 0.10 \cdot 1000 \cdot 2)}{1000}$$
$$G_1 = \frac{240 - 80 - 0.8}{1000} = \frac{159.2}{1000} = 0.1592$$

$$G_2 = -\frac{15^2}{2 \cdot 1000^2} = -\frac{225}{2000000} = -0.0001125$$

$$G_3 = -\frac{0.0894^2 \cdot (0.10 \cdot 1000 \cdot 2 \cdot 3)^2}{2 \cdot 1000^2} = -\frac{0.00799 \cdot 360000}{2000000} \approx -0.001438$$

$$G = 0.1592 - 0.0001125 - 0.001438 \approx 0.1577$$

The strategy returns approximately $15.77\%$ capital growth per trade. $G > 0$, so it clears the feasibility threshold comfortably.

Now observe what happens with a poorly backtested strategy — same parameters but $n = 10$ trades:

$$\sigma_\omega = \sqrt{\frac{0.60 \cdot 0.40}{10}} \approx 0.1549$$

$$G_3 = -\frac{0.1549^2 \cdot 360000}{2000000} = -\frac{0.02399 \cdot 360000}{2000000} \approx -0.004318$$

$$G \approx 0.1592 - 0.0001125 - 0.004318 \approx 0.1548$$

Still positive here, but the win rate uncertainty drag has grown threefold. For a strategy with a thinner edge, a 10-trade backtest could easily push $G$ below zero — making it appear feasible on paper while being demonstrably unviable under scrutiny.

And one final check, let's consider $n = 10000$ trades, same parameters:

$$\sigma_\omega = \sqrt{\frac{0.60 \cdot 0.40}{10000}} \approx 0.0049$$

$$G_3 = -\frac{0.0049^2 \cdot 360000}{2000000} = -\frac{0.00002401 \cdot 360000}{2000000} \approx -0.00000432$$

$$G \approx 0.1592 - 0.0001125 - 0.00000432 \approx 0.1591$$

Similar result to $n = 30$, just with much smaller winrate uncertainty drag.
This is why backtest sample size is not a technicality. It is a direct input to $G$.

## 6. Conclusion

We have managed to construct a unified mathematical framework for evaluating the long-term viability of a crypto trading strategy, all from a simple EV per trade formula not accounting for fees.

If you'd like to try to get your $G$ with some backtested data, but don't want to type the lengthy formula by hand, you can use [this script](G_script.py) right here. Simply open it, adjust parameters, run `python G_script.py` in the directory the script is located in, and you will see your $G$.