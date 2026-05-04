import socket
import json
import time
import os
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from strategy import SMACrossoverStrategy

def load_config():
    config = {}
    with open('api.txt', 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                config[key.strip()] = value.strip()
    return config

class LivenodeBot:
    def __init__(self, symbol="SPY"):
        self.config = load_config()
        self.symbol = symbol
        self.strategy = SMACrossoverStrategy()
        self.socket_port = 5555
        self.socket_host = '127.0.0.1'
        
        # Initialize clients
        self.data_client = StockHistoricalDataClient(
            self.config['API'], self.config['SECRET']
        )
        self.stream_client = StockDataStream(
            self.config['API'], self.config['SECRET']
        )

    def send_signal(self, side):
        print(f"Sending {side} signal for {self.symbol} to C++ engine...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.socket_host, self.socket_port))
                message = json.dumps({
                    "symbol": self.symbol,
                    "side": side,
                    "qty": 1, # Default to 1 share for paper trading demo
                    "type": "market"
                })
                s.sendall(message.encode())
                response = s.recv(1024)
                print(f"C++ Response: {response.decode()}")
        except ConnectionRefusedError:
            print("Error: C++ execution engine is not running!")

    async def on_bar(self, bar):
        print(f"New Bar: {bar.timestamp} | Close: {bar.close}")
        self.strategy.update(bar)
        signal = self.strategy.get_signal()
        if signal:
            self.send_signal(signal)

    def run(self):
        print(f"Starting Livenode Bot for {self.symbol}...")
        # Warm up strategy with some historical data
        print("Warming up with historical data...")
        request_params = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=TimeFrame.Minute,
            start=pd.Timestamp.now() - pd.Timedelta(hours=2)
        )
        bars = self.data_client.get_stock_bars(request_params)
        for bar in bars[self.symbol]:
            self.strategy.update(bar)
        
        # Start streaming
        self.stream_client.subscribe_bars(self.on_bar, self.symbol)
        self.stream_client.run()

if __name__ == "__main__":
    import asyncio
    import pandas as pd
    bot = LivenodeBot("AAPL") # Default to AAPL
    bot.run()
