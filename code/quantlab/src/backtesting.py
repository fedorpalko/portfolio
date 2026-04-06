# backtesting module for trading strategies (refactored and cleaned)
from typing import Tuple, Dict, Optional
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy import generate_signals
from downloader import download_data
from risk import calculate_risk_metrics, format_trades_list


def _apply_signals_and_returns(df: pd.DataFrame, initial_capital: float, params: dict = None) -> pd.DataFrame:
    """Apply strategy signals to compute position, returns, and portfolio value."""
    if 'signal' not in df.columns:
        df = generate_signals(df, params)

    df = df.copy()
    df['position'] = df['signal'].shift(1).fillna(0).astype(int)
    df['returns'] = df['close'].pct_change() * df['position']
    df['cumulative_returns'] = (1 + df['returns']).cumprod() * initial_capital
    return df


def _extract_trades(df: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
    """Extract discrete trades (entry/exit), PnL (dollars and pct), and duration."""
    trades = []
    prev_pos = 0
    entry = None
    cum_shifted = df['cumulative_returns'].shift(1).fillna(initial_capital)

    for idx, row in df.iterrows():
        pos = int(row['position'])
        price = float(row['close'])

        if prev_pos == 0 and pos != 0:
            entry = {'entry_date': idx, 'entry_price': price, 'entry_sign': pos, 'capital_entry': float(cum_shifted.loc[idx])}
        elif prev_pos != 0 and pos != prev_pos:
            if entry is not None:
                exit_price = price
                entry_price = entry['entry_price']
                sign = entry['entry_sign']
                pct = (exit_price / entry_price - 1.0) * sign
                pnl_dollars = pct * entry['capital_entry']
                duration = (idx - entry['entry_date']).days if hasattr(idx, 'day') else None # Re-inserted line
                # Calculate position size (number of units/shares)
                # Assuming capital_entry is fully used to buy/sell at entry_price
                position_size = entry['capital_entry'] / entry_price if entry_price != 0 else np.nan

                exit_reason = "Signal Flip" # Trade closed due to signal change
                
                trades.append({
                    'entry_date': entry['entry_date'],
                    'exit_date': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'sign': sign,
                    'pnl_pct': pct,
                    'pnl_dollars': pnl_dollars,
                    'duration_days': duration,
                    'position_size': position_size,
                    'exit_reason': exit_reason
                })
                entry = None
            if pos != 0:
                entry = {'entry_date': idx, 'entry_price': price, 'entry_sign': pos, 'capital_entry': float(df['cumulative_returns'].loc[idx])}

        prev_pos = pos

    if entry is not None:
        last_idx = df.index[-1]
        last_price = float(df['close'].iloc[-1])
        entry_price = entry['entry_price']
        sign = entry['entry_sign']
        pct = (last_price / entry_price - 1.0) * sign
        pnl_dollars = pct * entry['capital_entry']
        duration = (last_idx - entry['entry_date']).days if hasattr(last_idx, 'day') else None
        
        # Calculate position size for the last open trade
        position_size = entry['capital_entry'] / entry_price if entry_price != 0 else np.nan
        exit_reason = "End of Backtest" # Trade closed at the end of the backtest

        trades.append({
            'entry_date': entry['entry_date'],
            'exit_date': last_idx,
            'entry_price': entry_price,
            'exit_price': last_price,
            'sign': sign,
            'pnl_pct': pct,
            'pnl_dollars': pnl_dollars,
            'duration_days': duration,
            'position_size': position_size,
            'exit_reason': exit_reason
        })

    return pd.DataFrame(trades)


def format_summary(metrics: Dict[str, float], initial_capital: float) -> Dict[str, str]:
    """Format a comprehensive backtest summary into a dictionary of strings."""
    
    # Helper for formatting percentages
    def pct(val):
        return f"{val:.2f}%" if pd.notna(val) else "N/A"

    # Helper for formatting dollar amounts
    def dlr(val):
        return f"${val:,.2f}" if pd.notna(val) else "N/A"

    # Add initial capital to metrics dict for consistent formatting
    metrics['initial_capital'] = initial_capital

    formatted_metrics = {
        "Initial Capital": dlr(metrics['initial_capital']),
        "Final Capital": dlr(metrics['final_capital']),
        "Total Return": f"{pct(metrics['total_return_pct'])} ({dlr(metrics['pnl_total_dollars'])})",
        "Net Profit": dlr(metrics['net_profit_dollars']),
        "Gross Profit": dlr(metrics['gross_profit_dollars']),
        "Buy & Hold Return": pct(metrics['benchmark_cagr_pct']),
        "CAGR": pct(metrics['cagr_pct']),
        "Annualized Return": pct(metrics['annualized_return_pct']),
        "Profit Factor": f"{metrics['profit_factor']:.2f}" if pd.notna(metrics['profit_factor']) else "N/A",
        "Expectancy": f"{dlr(metrics['expectancy_dollars'])} ({pct(metrics['expectancy_pct'])})",
        "Win Rate": pct(metrics['win_rate_pct']),
        "Avg. Win / Avg. Loss": f"{dlr(metrics['avg_win_dollars'])} / {dlr(metrics['avg_loss_dollars'])}",
        "Win/Loss Ratio": f"{metrics['win_loss_ratio']:.2f}" if pd.notna(metrics['win_loss_ratio']) else "N/A",
        "Best Trade": f"{pct(metrics['best_trade_pct'])} ({dlr(metrics['best_trade_dollars'])})",
        "Worst Trade": f"{pct(metrics['worst_trade_pct'])} ({dlr(metrics['worst_trade_dollars'])})",
        "Max Drawdown": f"{pct(metrics['max_drawdown_pct'])} ({dlr(metrics['max_drawdown_dollars'])})",
        "Max Drawdown Duration": f"{metrics['max_drawdown_duration_days']:.1f} days" if pd.notna(metrics['max_drawdown_duration_days']) else "N/A",
        "Average Drawdown": pct(metrics['avg_drawdown_pct']),
        "Avg. Drawdown Duration": f"{metrics['avg_drawdown_duration_days']:.1f} days" if pd.notna(metrics['avg_drawdown_duration_days']) else "N/A",
        "Annualized Volatility": pct(metrics['volatility_pct']),
        "Downside Volatility": pct(metrics['downside_volatility_pct']),
        "Value at Risk (VaR 95%)": pct(metrics['var_pct']),
        "Cond. VaR (CVaR 95%)": pct(metrics['cvar_pct']),
        "Total Fees Paid": dlr(metrics['total_fees_paid']),
        "Slippage Impact": f"{dlr(metrics['slippage_impact'])}", # (placeholder)
        "Break-even Win Rate": pct(metrics['break_even_win_rate_pct']),
        "Sharpe Ratio": f"{metrics['sharpe']:.3f}" if pd.notna(metrics['sharpe']) else "N/A",
        "Sortino Ratio": f"{metrics['sortino']:.3f}" if pd.notna(metrics['sortino']) else "N/A",
        "Calmar Ratio": f"{metrics['calmar']:.3f}" if pd.notna(metrics['calmar']) else "N/A",
        "Return / Max DD Ratio": f"{metrics['return_max_dd_ratio']:.2f}" if pd.notna(metrics['return_max_dd_ratio']) else "N/A",
        "Total Trades": f"{metrics['trades_count']}",
        "Trades Per Year": f"{metrics['trades_per_year']:.1f}" if pd.notna(metrics['trades_per_year']) else "N/A",
        "Avg. Trade Duration": f"{metrics['avg_trade_duration_days']:.1f} days" if pd.notna(metrics['avg_trade_duration_days']) else "N/A",
        "Long/Short Exposure": f"{pct(metrics['long_exposure_pct'])} / {pct(metrics['short_exposure_pct'])}",
        "Time in Market": pct(metrics['time_in_market_pct']),
        "Max Consecutive Wins": f"{metrics['max_consecutive_wins']}",
        "Max Consecutive Losses": f"{metrics['max_consecutive_losses']}",
        "Equity Curve Slope (R^2)": f"{metrics['equity_curve_slope']:.4f} ({metrics['stability_of_returns_r2']:.3f})"
    }
    
    return formatted_metrics

def format_metrics_dataframe(formatted_metrics: Dict[str, str]) -> pd.DataFrame:
    """Converts the formatted metrics dictionary into a DataFrame for display."""
    df = pd.DataFrame.from_dict(formatted_metrics, orient='index', columns=['Value'])
    df.index.name = 'Metric'
    return df


def _plot_results(df: pd.DataFrame, 
                  trades_df: pd.DataFrame, 
                  benchmark_df: pd.DataFrame,
                  ticker: str, 
                  start_date: str, 
                  end_date: str, 
                  initial_capital: float, # Added initial_capital parameter
                  return_fig: bool = False) -> Optional[plt.Figure]:
    """Plot cumulative returns and mark trade entries/exits."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot strategy returns
    ax.plot(df.index, df['cumulative_returns'], label='Strategy Returns', color='b', lw=2)
    
    # Plot benchmark (buy and hold)
    initial_close = benchmark_df['close'].iloc[0]
    benchmark_returns = (benchmark_df['close'] / initial_close) * initial_capital
    ax.plot(benchmark_df.index, benchmark_returns, label=f'Buy & Hold ({ticker})', color='grey', ls='--', lw=1.5)

    # Mark trades
    if len(trades_df) > 0:
        entry_dates = trades_df['entry_date']
        exit_dates = trades_df['exit_date']
        ax.scatter(entry_dates, df.loc[entry_dates, 'cumulative_returns'], marker='^', color='g', s=100, label='Entry', zorder=5)
        ax.scatter(exit_dates, df.loc[exit_dates, 'cumulative_returns'], marker='v', color='r', s=100, label='Exit', zorder=5)
        
    ax.set_title('Cumulative Returns: Strategy vs. Buy & Hold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Portfolio Value ($)')
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    if return_fig:
        return fig
        
    if plt.isinteractive():
        plt.show()
    else:
        os.makedirs('plots', exist_ok=True)
        filename = f'plots/backtest_{ticker}_{start_date}_{end_date}.png'
        plt.savefig(filename)
        print(f"Plot saved as '{filename}'")
        plt.close(fig)
    return None


def backtest_strategy(initial_capital: float = 10000.0,
                      ticker: str = "AAPL",
                      start_date: str = "2020-01-01",
                      end_date: str = "2023-01-01",
                      period: str = "1d",
                      show_plot: bool = True,
                      fees_per_trade: float = 0.0,
                      params: dict = None) -> Tuple[pd.DataFrame, Dict[str, float], pd.DataFrame, Optional[plt.Figure]]:
    """Run backtest and return (df, metrics, trades_df, and optional fig).

    Set `show_plot=True` to generate and return the cumulative returns plot.
    """
    # Download data for strategy
    df = download_data(ticker, start_date, end_date, period)
    
    # Download data for benchmark (buy and hold)
    benchmark_df = df.copy() # The raw data is the benchmark

    # Run strategy logic
    df = generate_signals(df, params)
    df = _apply_signals_and_returns(df, initial_capital, params)

    # Extract trades and calculate all metrics
    trades_df = _extract_trades(df, initial_capital)
    metrics = calculate_risk_metrics(df, trades_df, initial_capital, benchmark_df=benchmark_df, fees_per_trade=fees_per_trade)

    # Format and print the summary report
    summary_report = format_summary(metrics, initial_capital)
    print(summary_report)

    # Format and print the trades list
    trades_list_report = format_trades_list(trades_df)
    print(trades_list_report)

    fig = None
    if show_plot:
        fig = _plot_results(df, trades_df, benchmark_df, ticker, start_date, end_date, initial_capital, return_fig=True)

    return df, metrics, trades_df, fig