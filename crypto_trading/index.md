# Crypto Trading

This section of the portfolio documents my journey through trading cryptocurrency.
It includes strategy design theorems and theses.

### Strategies

Strategies are grounded to specific mathematical standards and quotas that they need to pass in order to be standard-certified. A key criterion is $G$, which is defined in the Universal Growth Rate Model paper found below.

[**Gamma ($\gamma$)**](strats/Gamma.md) is a trading strategy designed for institutions to grow capital with consistently low drawdown using trend following.\

### Papers

I have also written a few mathematical papers related to day trading.

[**Universal Growth Rate Model**](papers/EV_paper.md) - This paper introduces the mathematical framework for evaluating and comparing trading strategies.

### Tools

The [**G Calculator**](tools/G_script.py) is a minimal standalone Python script for computing $G$ from raw strategy parameters — no dependencies required. For a full interactive experience with Monte Carlo simulation and Kelly sizing, see [**Tradelab**](../code/tradelab/README.md) in the code projects.