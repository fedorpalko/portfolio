import json
import time
import os
import pandas as pd
import socket
import importlib
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

def load_config():
    config = {}
    with open('api.txt', 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                config[key.strip().upper()] = value.strip()
    return config

def load_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

class LivenodeBot:
    def __init__(self):
        self.config = load_config()
        self.settings = load_settings()
        self.pairlist = self.settings['pairlist']
        self.timeframe_str = self.settings['timeframe']
        
        # Load Strategy
        strategy_name = self.settings['strategy']
        module = importlib.import_module(f"strategies.{strategy_name}")
        self.strategy = module.Strategy(**self.settings.get('strategy_params', {}))
        
        self.socket_port = 5555
        self.socket_host = '127.0.0.1'
        
        # Initialize clients
        self.data_client = StockHistoricalDataClient(
            self.config['API'], self.config['SECRET']
        )
        self.stream_client = StockDataStream(
            self.config['API'], self.config['SECRET']
        )

    def get_timeframe(self):
        mapping = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, TimeFrame.Minute),
            "15Min": TimeFrame(15, TimeFrame.Minute),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day
        }
        return mapping.get(self.timeframe_str, TimeFrame.Minute)

    def send_signal(self, symbol, side):
        print(f"[{symbol}] Sending {side} signal to C++ engine...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.socket_host, self.socket_port))
                message = json.dumps({
                    "symbol": symbol,
                    "side": side,
                    "qty": 1, 
                    "type": "market"
                })
                s.sendall(message.encode())
                response = s.recv(1024)
                print(f"[{symbol}] C++ Response: {response.decode()}")
        except ConnectionRefusedError:
            print(f"[{symbol}] Error: C++ execution engine is not running!")

    async def on_bar(self, bar):
        print(f"[{bar.symbol}] New Bar: {bar.timestamp} | Close: {bar.close}")
        self.strategy.update(bar)
        signal = self.strategy.get_signal(bar.symbol)
        if signal:
            self.send_signal(bar.symbol, signal)

    def run(self):
        print(f"Starting Livenode Bot with strategy: {self.settings['strategy']}")
        print(f"Pairs: {', '.join(self.pairlist)}")
        
        # Warm up strategy with historical data
        print("Warming up with historical data...")
        request_params = StockBarsRequest(
            symbol_or_symbols=self.pairlist,
            timeframe=self.get_timeframe(),
            start=pd.Timestamp.now(tz='UTC') - pd.Timedelta(hours=5),
            feed=DataFeed.IEX
        )
        bars = self.data_client.get_stock_bars(request_params)
        
        # Process historical bars symbol by symbol
        for symbol in self.pairlist:
            if symbol in bars.data:
                for bar in bars.data[symbol]:
                    # Inject symbol into bar if not present (alpaca-py sometimes varies here)
                    if not hasattr(bar, 'symbol'):
                        bar.symbol = symbol
                    self.strategy.update(bar)
        
        # Start streaming
        self.stream_client.subscribe_bars(self.on_bar, *self.pairlist)
        self.stream_client.run()

if __name__ == "__main__":
    bot = LivenodeBot()
    bot.run()
