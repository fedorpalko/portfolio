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
- Capital is defined as $C = 1,000,000$
- Fees are defined as $f_e = f_x = 0$ due to Kraken's zero maker fee policy on limit orders for high volume traders (who we are)
- Leverage is set at $L=2$
- We are trading futures pairs using limit orders on Kraken

## 2. Deploying $G$ and locating the thresholds for $\bar{\omega}$, $\bar{R}$ and $\sigma$

The goal here is to once again identify the must-have constraints that Delta must satisfy in order to live up to its purpose.

We also utilize Beta distribution for $\bar{\omega}$ and uniform distribution for $\bar{R}$, as in Gamma. The approach is pretty similar across all strategies built using the UGRM.

$$\bar{\omega} \sim \text{Beta}(\alpha, \beta), \quad \alpha = 4,\ \beta = 5.5$$
This yields a prior mean of:

$$\mathbb{E}[\bar{\omega}] = \frac{\alpha}{\alpha + \beta} = \frac{4}{9.5} \approx 0.421$$

And then for reward:

$$\bar{R} \sim \mathcal{U}(2, 3.5), \quad \mathbb{E}[\bar{R}] = 2.75$$

We change the $G_{goal}$ here, setting it to $0.02$ to differentiate from Gamma.