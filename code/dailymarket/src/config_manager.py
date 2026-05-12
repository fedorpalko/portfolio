import json
import os

class ConfigManager:
    def __init__(self, config_path="config.json", api_txt_path="../../api.txt"):
        self.config_path = config_path
        self.api_txt_path = api_txt_path
        self.config = {}
        self.api_key = ""
        self.load_config()
        self.load_api_key()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                "market_cap_limit": 500,
                "watchlist": [],
                "show_count": 10,
                "update_interval": 60
            }

    def load_api_key(self):
        # The script is in code/dailymarket/src/
        # api.txt is in code/dailymarket/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        search_paths = [
            os.path.join(current_dir, "..", "api.txt"),      # code/dailymarket/api.txt
            os.path.join(current_dir, "..", "..", "..", "api.txt"), # Development/portfolio/api.txt
            "api.txt"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        key = f.read().strip()
                        if key and "YOUR_ALPHAVANTAGE" not in key:
                            self.api_key = key
                            return
                except Exception:
                    continue
        
        self.api_key = ""
        print("Warning: AlphaVantage API key not found or placeholder used.")

    def get(self, key, default=None):
        self.load_config() # Reload for "on the fly" updates
        return self.config.get(key, default)
