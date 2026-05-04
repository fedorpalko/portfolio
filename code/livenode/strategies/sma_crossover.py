import pandas as pd

class Strategy:
    def __init__(self, fast_window=20, slow_window=50):
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.symbols_data = {} # Map symbol -> DataFrame
        self.positions = {}    # Map symbol -> current position (0 or 1)

    def update(self, bar):
        symbol = bar.symbol
        if symbol not in self.symbols_data:
            self.symbols_data[symbol] = pd.DataFrame()
            self.positions[symbol] = 0
            
        new_row = pd.DataFrame([{'timestamp': bar.timestamp, 'close': bar.close}])
        self.symbols_data[symbol] = pd.concat([self.symbols_data[symbol], new_row]).tail(self.slow_window + 1)
        
    def get_signal(self, symbol):
        """
        Returns 'buy', 'sell', or None.
        """
        data = self.symbols_data.get(symbol)
        if data is None or len(data) < self.slow_window:
            return None

        closes = data['close']
        fast_sma = closes.rolling(window=self.fast_window).mean()
        slow_sma = closes.rolling(window=self.slow_window).mean()

        # Check for crossover
        if fast_sma.iloc[-1] > slow_sma.iloc[-1] and fast_sma.iloc[-2] <= slow_sma.iloc[-2]:
            if self.positions[symbol] == 0:
                self.positions[symbol] = 1
                return 'buy'
        
        elif fast_sma.iloc[-1] < slow_sma.iloc[-1] and fast_sma.iloc[-2] >= slow_sma.iloc[-2]:
            if self.positions[symbol] == 1:
                self.positions[symbol] = 0
                return 'sell'
        
        return None
