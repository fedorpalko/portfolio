# IMC Prosperity 2026 Tutorial Round 1

In this section I shall showcase my algorithms, store datasets and also explain each strategy and what it is.

### Emerald Strategy

The link to this strategy is [here](emerald.py), if you wish to see the specific code.
In terms of trading emeralds, there were several issues I faced: in some iterations, we would make no trades because IMC's bots got to them first, in other strategies we couldn't make enough because of us having to go at different prices due to the bots. Showcasing here in a format of vX (buy price/sell price), where X is version number:

- v1 (9999/10001) — Got 29 fills but captured only 2-tick spread. The fills came from market trades matching against our resting quotes, not from the order book. Made basically nothing.
- v2 (9992/10008) — Zero fills. We sat at the exact same price as the bots but behind them in queue. They absorbed all flow before it reached us.
- v3 (9993/10007) — One tick inside the bots. We now have price priority over them, so incoming market orders hit our quotes first. This iteration proved to be the most successful so far!
