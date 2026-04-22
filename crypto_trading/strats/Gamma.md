**Author:** Fedor Palko\
**Date started:** 20/04/2026

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

## 1. Setting Boundaries

#### 1.1. Exploring potential trading approaches

There are several trading approaches in crypto, each with its own traits. I will outline the most common ones and then decide what we are going for:

- **Scalping**: high trade count, low holding time can lead to fee drag, and it's not really suitable for institutions, even though machine precision definitely helps with scalping. It's simply not responsible.
- **Breakout:** low trade count, low win rate, high reward, relies on finding the right move. Very similar to gambling, requires high conviction which rarely happens.