The **WSLAB** (Wall Street Lab) project is a TUI backtester and Bayesian optimization engine for stock market strategies and algotraders built using the `backtesting.py` Python library.

> This project is a simulation: it doesn't directly translate to real-world profits, it's primarily a utility.

### Features

WSLAB is capable of several functions and tasks, including:
- Fully featured backtesting, powered by Yahoo Finance
- Bayesian optimization to find the best indicator parameters and better finetuning your strategy
- Simple integration with custom strategies via custom defined functions, like `longSignal` and `shortSignal`, which allow for easy strategy development
- Charting and plotting in HTML, powered by `backtesting.py` library functions

### First Steps

There are two methods of starting up WSLAB for yourself: the automated script, and the manual setup. Both methods require being located in the root directory of WSLAB.

#### Script

WSLAB does come with a built-in setup script, which can be started with `chmod +x setup.sh &&./setup.sh`. The script will perform the following:
- Create a virtual environment
- Install required dependencies

Once setup is complete, you can execute the app via `venv/bin/python src/main.py` when you wish.

#### Manual Installation

Joke's on you, if you want to do it manually, you can, it's not that difficult - basically replicate the script functionalities.
I will not provide additional information.