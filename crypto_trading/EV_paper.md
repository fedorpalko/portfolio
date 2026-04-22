## Universal Growth Rate Model

**Author:** Fedor Palko\
**Date started:** 21/04/2026

## Thesis

In this paper I hope to explore and build upon a standalone and simple EV per trade formula, where I eventually hope to define $G$ as the standard ultimate universal growth rate model - basically the % of which your stake will grow each trade. $G$ accounts for compounding, fee drag, volatility and win rate uncertainty. I want to do it in a way where it is both simple enough to be understood by anyone and yet complex enough to be statistically sound and useful for actual trading strategies, including my own.

## Sections

1. EV Uniform Model
2. EV Uniform Model (Fees and Commission)
3. EV Volatile Model
4. EV Volatile Model (Uncertain Winrate)
5. Universal Growth Rate Model
6. Conclusion

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

Compared to our initial UM result, we have achieved a result that while only $0,4 smaller, imagine what this could do at a strategy trading with $50 million. The fee would be $400,000. Astronomical. Further sections will further demonstrate how to rigorously account for fees and fee drag.

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

As we can see, $\tilde{\rho}$ is not a fixed number, but a random variable and more importantly, a random distribution. It's a different level from sections 1 and 2, where we worked with discrete math. But if you think this is scary, you ain't seen nothing yet.