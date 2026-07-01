Welcome to **Fincli**. Below is a quick guide on how to get started using it.

> This app merely returns data from Yahoo Finance, it doesn't directly translate to trading advice.

### Features

- Create watchlists of your favorite symbols
- A live, auto-refreshing quote table (price, daily change, % change, market cap)
- Automatic refresh interval configurable in-app or in the settings file
- Editable settings (refresh rate, accent color, columns) without leaving the terminal
- Up-to-date stock prices, no strings attached, free forever

### Getting Started

To configure Fincli, run the following command: `chmod +x setup.sh && ./setup.sh`, then run Fincli via `venv/bin/python src/main.py`.

### Using Fincli

The main menu offers:

1. **Live watchlist** — an auto-refreshing table; press `Ctrl+C` to return to the menu.
2. **Manage watchlist** — add or remove symbols (new symbols are verified against Yahoo Finance before being saved).
3. **Settings** — edit the refresh interval, accent color, and whether the market-cap column is shown.

All preferences live in `config.json` next to `setup.sh`. You can edit that file directly or change everything from the in-app **Settings** screen — changes are saved immediately.
