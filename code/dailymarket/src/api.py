import requests
import time
import pandas as pd
from datetime import datetime, timedelta

class AlphaVantageClient:
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = {}
        self.last_call_time = 0
        self.rate_limit_delay = 12.1 # Slightly > 12s for 5 calls/min

    def _throttle(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_call_time = time.time()

    def _get(self, params):
        if self.api_key == "YOUR_ALPHAVANTAGE_API_KEY_HERE" or not self.api_key:
            return None
        
        params["apikey"] = self.api_key
        self._throttle()
        try:
            response = requests.get(self.BASE_URL, params=params)
            data = response.json()
            if "Note" in data:
                print("AlphaVantage Rate Limit Reached. Waiting...")
                time.sleep(60)
                return self._get(params)
            return data
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def get_top_movers(self):
        params = {"function": "TOP_GAINERS_LOSERS"}
        return self._get(params)

    def get_symbol_performance(self, symbol):
        if symbol in self.cache:
            last_fetch, data = self.cache[symbol]
            if datetime.now() - last_fetch < timedelta(hours=1):
                return data

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact"
        }
        data = self._get(params)
        if not data or "Time Series (Daily)" not in data:
            return None

        series = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(series, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df = df.sort_index(ascending=False)

        # Calculate performance
        try:
            current_price = df.iloc[0]["4. close"]
            
            # 24h (1 day ago)
            prev_24h = df.iloc[1]["4. close"] if len(df) > 1 else current_price
            perf_24h = ((current_price - prev_24h) / prev_24h) * 100

            # 48h (2 days ago)
            prev_48h = df.iloc[2]["4. close"] if len(df) > 2 else prev_24h
            perf_48h = ((current_price - prev_48h) / prev_48h) * 100

            # 7d (approx 5 trading days ago)
            prev_7d = df.iloc[min(5, len(df)-1)]["4. close"] if len(df) > 1 else current_price
            perf_7d = ((current_price - prev_7d) / prev_7d) * 100

            result = {
                "symbol": symbol,
                "price": current_price,
                "24h": perf_24h,
                "48h": perf_48h,
                "7d": perf_7d
            }
            self.cache[symbol] = (datetime.now(), result)
            return result
        except Exception as e:
            print(f"Error calculating performance for {symbol}: {e}")
            return None
