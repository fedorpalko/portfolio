# Tradelab

Tradelab is a Terminal User Interface (TUI) application designed to determine trading strategy viability in real-time trading. It implements the **Universal Growth Rate ($G$)** model, accounting for fee drag, volatility, and win rate uncertainty.

## Features

- **Universal Growth Model**: Calculates $G$, the geometric growth rate of your capital per trade.
- **Monte Carlo Simulations**: Visualizes potential equity paths and calculates Risk of Ruin (RoR).
- **Kelly Criterion**: Suggests optimal position sizing based on your strategy edge.
- **Interactive TUI**: Adjust parameters on the fly and see real-time updates.
- **JSON Persistence**: Save and load strategy parameters.

## Installation

1. Ensure you have Python 3.8+ installed.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   venv/bin/pip install -r requirements.txt
   ```

## Usage

Run the application using:
```bash
venv/bin/python src/main.py
```

## Mathematical Foundation

The core logic is based on the formula:
$$G = G_1 + G_2 + G_3$$
Where:
- $G_1$: Base growth rate (edge minus fees).
- $G_2$: Volatility drag penalty.
- $G_3$: Win rate uncertainty drag penalty.

If $G > 0$, the strategy is mathematically viable over the long run.
