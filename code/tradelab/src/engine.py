import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class StrategyParams:
    win_rate: float  # omega (0 to 1)
    reward_ratio: float  # R_bar (e.g. 2.0 for 1:2)
    capital: float  # C (total trading capital)
    leverage: float  # L
    sample_size: int  # n (number of trades in backtest)
    std_dev: float  # sigma (P&L std dev in currency)
    entry_fee: float  # f_e (as decimal, e.g. 0.001)
    exit_fee: float  # f_x
    position_size: float  # S (fraction of capital, 0 to 1)
    trades_per_year: int = 52  # for CAGR projection

    def to_json(self):
        return json.dumps(asdict(self), indent=4)

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)

class UniversalGrowthModel:
    @staticmethod
    def calculate_g(p: StrategyParams) -> Dict[str, float]:
        # omega_sigma = sqrt(omega * (1 - omega) / n)
        omega_sigma = np.sqrt(p.win_rate * (1 - p.win_rate) / p.sample_size)
        
        # G1: Base growth rate (normalized edge - fees)
        # G1 = S * L * [omega * R_bar - (1 - omega) - (f_e + f_x)]
        g1 = p.position_size * p.leverage * (
            p.win_rate * p.reward_ratio - (1 - p.win_rate) - (p.entry_fee + p.exit_fee)
        )
        
        # G2: Volatility drag
        # G2 = -sigma^2 / (2 * C^2)
        g2 = -(p.std_dev**2) / (2 * (p.capital**2))
        
        # G3: Win rate uncertainty drag
        # G3 = - (omega_sigma^2 * (S * L * (R_bar + 1))^2) / 2
        # (C^2 cancels out in the fractional form)
        g3 = -(omega_sigma**2 * (p.position_size * p.leverage * (p.reward_ratio + 1))**2) / 2
        
        g_total = g1 + g2 + g3
        
        return {
            "g1": g1,
            "g2": g2,
            "g3": g3,
            "g_total": g_total,
            "omega_sigma": omega_sigma
        }

    @staticmethod
    def calculate_kelly(p: StrategyParams) -> float:
        # f* = (p * b - q) / b
        # where p = win_rate, q = 1-p, b = reward_ratio
        # f* = (win_rate * reward_ratio - (1 - win_rate)) / reward_ratio
        # This is for base RR. Including fees:
        adjusted_rr = p.reward_ratio - (p.entry_fee + p.exit_fee)
        kelly = (p.win_rate * adjusted_rr - (1 - p.win_rate)) / adjusted_rr
        return max(0.0, kelly)

    @staticmethod
    def breakeven_analysis(p: StrategyParams) -> Dict[str, float]:
        """
        Calculates the minimum win rate and minimum R:R for G to reach exactly zero,
        holding all other parameters fixed. Drag terms (G2, G3) are computed at the
        current parameter values and treated as constants in the inversion.
        """
        results = UniversalGrowthModel.calculate_g(p)
        drag = -(results['g2'] + results['g3'])  # positive total drag

        sl = p.position_size * p.leverage
        fees = p.entry_fee + p.exit_fee

        # G1 = drag  =>  sl * (omega * (R+1) - 1 - fees) = drag
        # omega_min = (drag/sl + 1 + fees) / (R+1)
        if sl > 0:
            win_rate_min = (drag / sl + 1 + fees) / (p.reward_ratio + 1)
            win_rate_min = float(np.clip(win_rate_min, 0.0, 1.0))
        else:
            win_rate_min = float('nan')

        # G1 = drag  =>  sl * (omega * R - (1-omega) - fees) = drag
        # R_min = (drag/sl + (1-omega) + fees) / omega
        if p.win_rate > 0 and sl > 0:
            rr_min = (drag / sl + (1 - p.win_rate) + fees) / p.win_rate
            rr_min = float(max(0.0, rr_min))
        else:
            rr_min = float('nan')

        win_rate_margin = p.win_rate - win_rate_min if not np.isnan(win_rate_min) else float('nan')
        rr_margin = p.reward_ratio - rr_min if not np.isnan(rr_min) else float('nan')

        return {
            'win_rate_min': win_rate_min,
            'rr_min': rr_min,
            'win_rate_margin': win_rate_margin,
            'rr_margin': rr_margin,
        }

    @staticmethod
    def monte_carlo_simulation(p: StrategyParams, num_paths: int = 100, num_trades: int = 500, ruin_threshold: float = 0.1) -> Dict:
        """
        Simulates equity paths. 
        ruin_threshold: Fraction of initial capital at which we consider the account ruined (default 10%).
        """
        omega_sigma = np.sqrt(p.win_rate * (1 - p.win_rate) / p.sample_size)
        
        paths = []
        terminal_values = []
        ruined_count = 0
        threshold = p.capital * ruin_threshold
        
        for _ in range(num_paths):
            # Draw a "true" win rate for this reality
            path_win_rate = np.random.normal(p.win_rate, omega_sigma)
            path_win_rate = np.clip(path_win_rate, 0, 1)
            
            equity = p.capital
            equity_path = [equity]
            
            for _ in range(num_trades):
                # Determine win or loss
                is_win = np.random.random() < path_win_rate
                
                # Base P&L calculation
                stake = p.position_size * equity * p.leverage
                
                if is_win:
                    pnl = stake * p.reward_ratio
                else:
                    pnl = -stake
                
                # Add fees
                pnl -= (p.entry_fee + p.exit_fee) * stake
                
                # Add noise
                noise = np.random.normal(0, p.std_dev * (equity / p.capital))
                
                equity += (pnl + noise)
                
                if equity <= threshold:
                    equity = max(0, equity)
                    ruined_count += 1
                    equity_path.append(equity)
                    equity_path.extend([equity] * (num_trades - len(equity_path) + 1))
                    break
                
                equity_path.append(equity)
                
            paths.append(equity_path)
            terminal_values.append(equity)
            
        terminal_values = np.array(terminal_values)
        
        # Calculate RoR and G simulated
        ror = ruined_count / num_paths
        
        # Avoid log(0)
        valid_terminals = terminal_values[terminal_values > 0]
        if len(valid_terminals) > 0:
            g_sim = np.mean(np.log(valid_terminals / p.capital) / num_trades)
        else:
            g_sim = -1.0

        return {
            "paths": paths,
            "mean_terminal": np.mean(terminal_values),
            "median_terminal": np.median(terminal_values),
            "ror": ror,
            "g_simulated": g_sim
        }
