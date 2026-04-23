# Crypto Trading

This section of the portfolio documents my journey through trading cryptocurrency.
It includes strategy design theorems and theses.

### Strategies

Strategies are grounded to specific mathematical standards and quotas that they need to pass in order to be standard-certified. A key criterion is $G$, which is defined in the Universal Growth Rate Model paper found below.

[**Gamma ($\gamma$)**](strats/Gamma.md) is a trading strategy designed for institutions to grow capital with consistently low drawdown using trend following.\
[**Delta ($\delta$)**](strats/Delta.md) is a strategy also designed for institutions to grow capital, but using more risk in favor of larger potential returns.\
[**Epsilon ($\epsilon$)**](strats/Epsilon.md) is a strategy not designed for institutions, but rather for individuals to grow small accounts moderately quickly using trend following.\
[**Iota ($\iota$)**](strats/Iota.md) is an ML-powered mean-reversion algorithm designed for individuals and institutions alike, growing any sort of capital consistently and moderately quickly.\
[**Theta ($\theta$)**](strats/Theta.md) is an astronomically high-risk, high-reward breakout strategy designed for individuals who want to grow their accounts as fast as possible while not caring about risk.

### Papers

I have also written a few mathematical papers related to day trading.

[**Universal Growth Rate Model**](EV_paper.md) - This paper introduces the mathematical framework for evaluating and comparing trading strategies.

### Tools

The [**Viability Calculator**](G_script.py) Python script allows you to find your $G$ based on inputted strategy parameters based on the universal growth rate model.