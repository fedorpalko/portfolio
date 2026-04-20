## Thesis

**Gamma ($\gamma$)** is a trading strategy grounded and built upon rigorous mathematical models. Instead of working with eyeballed win rates and risk-reward ratios, Gamma works in reverse: it uses an integration-based approach over uncertainty ranges to determine what win rate and R:R ratio a strategy **must** achieve in order to maximize **expected log-wealth growth** — the correct objective for compounding capital — given a fixed capital base, fee structure, and leverage. The strategy is designed for conservative capital growth and designed for institutions that want to grow their capital using cryptocurrency trading in a way that is both quantitative and yields more while risking less.

## Scheme

1. Setting boundaries: exploring potential trading approaches, defining fixed values, deciding the timeframe and crypto pairs to trade
2. Defining the mathematical model: $G$, integration, and defining a final set of criterion the Gamma strategy must pass to be mathematically viable.
3. Strategy theoretical implementation: taking the criterion from step 2 and choosing indicators, entry and exit conditions, and risk management rules to create a blueprint.
4. Strategy implementation in Python using the Freqtrade framework
5. Analysis of various backtests
6. Analysis of various paper trading runs
7. Analysis of interactive notebooks
8. Conclusion