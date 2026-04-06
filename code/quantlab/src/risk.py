# risk.py - functions for comprehensive risk and performance metrics calculation
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from scipy.stats import norm

# --- Constants ---
TRADING_DAYS_PER_YEAR = 252
DEFAULT_ROLLING_WINDOW = 60  # For rolling metrics, e.g., 3 months
DEFAULT_VAR_CONFIDENCE = 0.95

# --- Main Calculation Function ---

def calculate_risk_metrics(df: pd.DataFrame, 
                           trades_df: pd.DataFrame, 
                           initial_capital: float,
                           benchmark_df: pd.DataFrame = None,
                           fees_per_trade: float = 0.0) -> Dict[str, float]:
    """Compute a comprehensive set of portfolio, trade-level, and risk metrics."""
    # --- Basic Portfolio Metrics ---
    final_capital = float(df['cumulative_returns'].iloc[-1])
    pnl_total = final_capital - initial_capital
    pnl_pct_total = (final_capital / initial_capital - 1.0)
    
    total_duration_years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = ((final_capital / initial_capital) ** (1 / total_duration_years) - 1) if total_duration_years > 0 else 0.0
    
    daily_returns = df['returns'].dropna()
    ann_return = daily_returns.mean() * TRADING_DAYS_PER_YEAR # simple ann return
    
    # --- Trade Analysis ---
    trades_count = len(trades_df)
    if trades_count > 0:
        wins_df = trades_df[trades_df['pnl_dollars'] > 0]
        losses_df = trades_df[trades_df['pnl_dollars'] < 0]

        win_rate = len(wins_df) / trades_count
        avg_win = wins_df['pnl_dollars'].mean()
        avg_loss = losses_df['pnl_dollars'].mean()
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf

        gross_profit = wins_df['pnl_dollars'].sum()
        gross_loss = losses_df['pnl_dollars'].sum()
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else np.inf
        
        expectancy_dollars = trades_df['pnl_dollars'].mean()
        expectancy_pct = trades_df['pnl_pct'].mean()
        
        best_trade_pct = trades_df['pnl_pct'].max()
        worst_trade_pct = trades_df['pnl_pct'].min()
        best_trade_abs = trades_df['pnl_dollars'].max()
        worst_trade_abs = trades_df['pnl_dollars'].min()
        
        avg_duration_days = trades_df['duration_days'].mean()
        trades_per_year = trades_count / total_duration_years if total_duration_years > 0 else 0
        
        long_trades = (trades_df['sign'] == 1).sum()
        short_trades = (trades_df['sign'] == -1).sum()
        long_exposure_pct = long_trades / trades_count if trades_count > 0 else 0
        short_exposure_pct = short_trades / trades_count if trades_count > 0 else 0

        # Consecutive wins/losses
        consecutive_wins, consecutive_losses = _calculate_consecutive_trades(trades_df['pnl_dollars'])

        # Cost & Efficiency
        total_fees_paid = trades_count * fees_per_trade
        pnl_total_from_trades = trades_df['pnl_dollars'].sum()
        net_profit = pnl_total_from_trades - total_fees_paid
        slippage_impact = 0.0 # Placeholder
        break_even_win_rate = abs(avg_loss) / (avg_win + abs(avg_loss)) if (avg_win + abs(avg_loss)) > 0 else 0.0

    else:
        win_rate, avg_win, avg_loss, win_loss_ratio, profit_factor, expectancy_dollars, \
        expectancy_pct, best_trade_pct, worst_trade_pct, best_trade_abs, worst_trade_abs, \
        avg_duration_days, trades_per_year, long_exposure_pct, short_exposure_pct, \
        consecutive_wins, consecutive_losses, total_fees_paid, net_profit, \
        slippage_impact, break_even_win_rate, gross_profit = [np.nan] * 22

    # --- Drawdown Analysis ---
    cum_returns = df['cumulative_returns']
    peaks = cum_returns.cummax()
    drawdowns = (cum_returns - peaks) / peaks
    max_drawdown = drawdowns.min() # Returns a negative value
    
    absolute_drawdowns = cum_returns - peaks
    max_drawdown_absolute = absolute_drawdowns.min()

    drawdown_periods = _calculate_drawdown_periods(drawdowns)
    avg_drawdown_pct = drawdown_periods['drawdown'].mean() if not drawdown_periods.empty else np.nan
    avg_drawdown_duration = drawdown_periods['duration'].mean() if not drawdown_periods.empty else np.nan
    max_drawdown_duration = drawdown_periods['duration'].max() if not drawdown_periods.empty else np.nan

    # --- Volatility and Risk-Adjusted Returns ---
    volatility = daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    downside_volatility = daily_returns[daily_returns < 0].std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    sharpe = (ann_return / volatility) if volatility != 0 else np.nan
    sortino = (ann_return / downside_volatility) if downside_volatility != 0 else np.nan
    calmar = (ann_return / abs(max_drawdown)) if max_drawdown != 0 else np.nan

    # --- Advanced Risk Metrics ---
    var, cvar = _calculate_var_cvar(daily_returns, confidence=DEFAULT_VAR_CONFIDENCE)

    # --- Market Comparison ---
    if benchmark_df is not None:
        benchmark_returns = benchmark_df['close'].pct_change().dropna()
        benchmark_cagr = ((benchmark_df['close'].iloc[-1] / benchmark_df['close'].iloc[0]) ** (1 / total_duration_years) - 1) if total_duration_years > 0 else 0.0
    else:
        benchmark_cagr = np.nan

    # --- Strategy Diagnostics ---
    time_in_market = (df['position'] != 0).sum() / len(df)
    
    # Rolling metrics
    rolling_sharpe = daily_returns.rolling(window=DEFAULT_ROLLING_WINDOW).mean() * TRADING_DAYS_PER_YEAR / \
                     (daily_returns.rolling(window=DEFAULT_ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS_PER_YEAR))
    
    rolling_drawdown = drawdowns.rolling(window=DEFAULT_ROLLING_WINDOW).min()

    # Equity curve analysis
    equity_slope, stability_of_returns = _analyze_equity_curve(cum_returns)


    return {
        # Performance
        'final_capital': final_capital,
        'pnl_total_dollars': pnl_total,
        'total_return_pct': pnl_pct_total * 100,
        'cagr_pct': cagr * 100,
        'annualized_return_pct': ann_return * 100,
        'benchmark_cagr_pct': benchmark_cagr * 100 if benchmark_df is not None else 'N/A',
        'profit_factor': profit_factor,
        'expectancy_dollars': expectancy_dollars,
        'expectancy_pct': expectancy_pct * 100,
        'win_rate_pct': win_rate * 100,
        'avg_win_dollars': avg_win,
        'avg_loss_dollars': avg_loss,
        'win_loss_ratio': win_loss_ratio,
        'best_trade_pct': best_trade_pct * 100,
        'worst_trade_pct': worst_trade_pct * 100,
        'best_trade_dollars': best_trade_abs,
        'worst_trade_dollars': worst_trade_abs,

        # Risk
        'max_drawdown_pct': abs(max_drawdown) * 100,
        'max_drawdown_dollars': max_drawdown_absolute,
        'max_drawdown_duration_days': max_drawdown_duration,
        'avg_drawdown_pct': abs(avg_drawdown_pct) * 100 if not np.isnan(avg_drawdown_pct) else np.nan,
        'avg_drawdown_duration_days': avg_drawdown_duration,
        'volatility_pct': volatility * 100,
        'downside_volatility_pct': downside_volatility * 100,
        'var_pct': abs(var) * 100,
        'cvar_pct': abs(cvar) * 100,

        # Risk-Adjusted Returns
        'sharpe': sharpe,
        'sortino': sortino,
        'calmar': calmar,
        'return_max_dd_ratio': pnl_pct_total / abs(max_drawdown) if max_drawdown != 0 else np.inf,

        # Trade Behavior
        'trades_count': trades_count,
        'trades_per_year': trades_per_year,
        'avg_trade_duration_days': avg_duration_days,
        'long_exposure_pct': long_exposure_pct * 100,
        'short_exposure_pct': short_exposure_pct * 100,
        'time_in_market_pct': time_in_market * 100,
        'max_consecutive_wins': consecutive_wins,
        'max_consecutive_losses': consecutive_losses,
        
        # Cost & Efficiency
        'total_fees_paid': total_fees_paid,
        'slippage_impact': slippage_impact,
        'net_profit_dollars': net_profit,
        'gross_profit_dollars': gross_profit,
        'break_even_win_rate_pct': break_even_win_rate * 100,

        # Diagnostics
        'equity_curve_slope': equity_slope,
        'stability_of_returns_r2': stability_of_returns,
        'rolling_sharpe': rolling_sharpe.iloc[-1] if not rolling_sharpe.empty else np.nan,
        'rolling_drawdown': rolling_drawdown.iloc[-1] if not rolling_drawdown.empty else np.nan,
        
        # Trade List Output
        'trade_list_output': format_trades_list(trades_df)
    }

# --- Helper Functions ---

def _calculate_drawdown_periods(drawdowns: pd.Series) -> pd.DataFrame:
    """Identifies and measures each distinct drawdown period."""
    in_drawdown = drawdowns < 0
    drawdown_periods = []
    start = None
    for idx, is_dd in in_drawdown.items():
        if is_dd and start is None:
            start = idx
        elif not is_dd and start is not None:
            period = drawdowns[start:idx]
            drawdown_periods.append({
                'start': start,
                'end': idx,
                'drawdown': period.min(),
                'duration': len(period)
            })
            start = None
    return pd.DataFrame(drawdown_periods)


def _calculate_var_cvar(returns: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Value at Risk (VaR) and Conditional VaR (CVaR)."""
    if returns.empty:
        return np.nan, np.nan
    var = returns.quantile(1 - confidence)
    cvar = returns[returns <= var].mean()
    return var, cvar


def _calculate_consecutive_trades(pnl: pd.Series) -> Tuple[int, int]:
    """Calculate the longest streak of winning and losing trades."""
    if pnl.empty:
        return 0, 0
    
    wins = pnl > 0
    losses = pnl < 0
    
    win_streaks = wins.cumsum() - wins.cumsum().where(~wins).ffill().fillna(0)
    loss_streaks = losses.cumsum() - losses.cumsum().where(~losses).ffill().fillna(0)
    
    return int(win_streaks.max()), int(loss_streaks.max())


def _analyze_equity_curve(equity: pd.Series) -> Tuple[float, float]:
    """Performs a linear regression on the equity curve to find its slope and R-squared."""
    if equity.empty:
        return np.nan, np.nan
        
    x = np.arange(len(equity))
    y = equity.values
    
    # y = mx + c
    m, c = np.polyfit(x, y, 1)
    
    # R-squared
    y_hat = m * x + c
    ss_res = ((y - y_hat)**2).sum()
    ss_tot = ((y - y.mean())**2).sum()
    
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    return m, r2

def format_trades_list(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Formats the list of trades into a Pandas DataFrame for display."""
    if trades_df.empty:
        return pd.DataFrame(columns=[
            'Entry Date', 'Exit Date', 'Type', 'Entry Price', 'Exit Price', 
            'Size', 'PnL ($)', 'PnL (%)', 'Duration (Days)', 'Exit Reason'
        ])

    trades_df = trades_df.copy()
    
    # Format columns for display
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.strftime('%Y-%m-%d')
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.strftime('%Y-%m-%d')
    trades_df['pnl_pct'] = (trades_df['pnl_pct'] * 100).map('{:.2f}%'.format)
    trades_df['pnl_dollars'] = trades_df['pnl_dollars'].map('${:,.2f}'.format)
    trades_df['trade_type'] = trades_df['sign'].apply(lambda x: 'Long' if x == 1 else 'Short')
    trades_df['entry_price'] = trades_df['entry_price'].map('{:,.2f}'.format)
    trades_df['exit_price'] = trades_df['exit_price'].map('{:,.2f}'.format)
    trades_df['position_size'] = trades_df['position_size'].astype(int)

    # Select and rename columns for the final output
    display_df = trades_df[[
        'entry_date', 
        'exit_date', 
        'trade_type',
        'entry_price', 
        'exit_price', 
        'position_size',
        'pnl_dollars', 
        'pnl_pct', 
        'duration_days',
        'exit_reason'
    ]]
    
    display_df = display_df.rename(columns={
        'entry_date': 'Entry Date',
        'exit_date': 'Exit Date',
        'trade_type': 'Type',
        'entry_price': 'Entry Price',
        'exit_price': 'Exit Price',
        'position_size': 'Size',
        'pnl_dollars': 'PnL ($)',
        'pnl_pct': 'PnL (%)',
        'duration_days': 'Duration (Days)',
        'exit_reason': 'Exit Reason'
    })

    return display_df
