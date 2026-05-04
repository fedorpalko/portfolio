import pandas as pd

class SMACrossoverStrategy:
    def __init__(self, fast_window=20, slow_window=50):
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.data = pd.DataFrame()
        self.position = 0  # 0: flat, 1: long

    def update(self, bar):
        """
        Update the internal data with a new bar.
        bar: dict with 't' (timestamp), 'c' (close)
        """
        new_row = pd.DataFrame([{'timestamp': bar.timestamp, 'close': bar.close}])
        self.data = pd.concat([self.data, new_row]).tail(self.slow_window + 1)
        
    def get_signal(self):
        """
        Returns 'buy', 'sell', or None.
        """
        if len(self.data) < self.slow_window:
            return None

        closes = self.data['close']
        fast_sma = closes.rolling(window=self.fast_window).mean()
        slow_sma = closes.rolling(window=self.slow_window).mean()

        # Check for crossover
        # Fast crossed above slow
        if fast_sma.iloc[-1] > slow_sma.iloc[-1] and fast_sma.iloc[-2] <= slow_sma.iloc[-2]:
            if self.position == 0:
                self.position = 1
                return 'buy'
        
        # Fast crossed below slow
        elif fast_sma.iloc[-1] < slow_sma.iloc[-1] and fast_sma.iloc[-2] >= slow_sma.iloc[-2]:
            if self.position == 1:
                self.position = 0
                return 'sell'
        
        return None
