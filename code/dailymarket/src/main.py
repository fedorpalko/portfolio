import time
import sys
import os
from config_manager import ConfigManager
from api import AlphaVantageClient
from display import DisplayManager

def main():
    # Fix paths for running from src or root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    
    config = ConfigManager(config_path=config_path)
    api = AlphaVantageClient(config.api_key)
    display = DisplayManager()

    while True:
        try:
            # Refresh config "on the fly"
            watchlist_symbols = config.get("watchlist", [])
            show_count = config.get("show_count", 10)
            update_interval = config.get("update_interval", 60)

            # 1. Fetch Watchlist Data
            watchlist_data = []
            for sym in watchlist_symbols:
                perf = api.get_symbol_performance(sym)
                if perf:
                    watchlist_data.append(perf)

            # 2. Fetch Top Movers (24h)
            movers = api.get_top_movers()
            gainers_data = []
            losers_data = []

            if movers:
                # Top Gainers
                top_gainers = movers.get("top_gainers", [])[:show_count]
                for g in top_gainers:
                    # Enrich with 48h and 7d data
                    perf = api.get_symbol_performance(g["ticker"])
                    if perf:
                        gainers_data.append(perf)
                
                # Top Losers
                top_losers = movers.get("top_losers", [])[:show_count]
                for l in top_losers:
                    perf = api.get_symbol_performance(l["ticker"])
                    if perf:
                        losers_data.append(perf)

            # 3. Render
            display.render(watchlist_data, gainers_data, losers_data)

            # 4. Wait
            time.sleep(update_interval)

        except KeyboardInterrupt:
            print("\nExiting Dailymarket...")
            sys.exit(0)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
