import streamlit as st
import json
import os
import sys
from datetime import datetime
import pandas as pd

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backtesting import backtest_strategy, format_summary, format_metrics_dataframe
from risk import format_trades_list
from optimizer import run_optimization
from strategy import DEFAULT_PARAM_RANGES

class StreamlitLogCapture:
    def __init__(self):
        self.log_messages = []

    def write(self, message):
        if message.strip(): # Only add non-empty messages
            self.log_messages.append(message)

    def flush(self):
        pass # Required for file-like objects

def load_config():
    """Loads configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(config):
    """Saves configuration to config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

st.set_page_config(page_title="Quantlab", layout="wide")



# Load config
config = load_config()

# Sidebar for configuration
st.sidebar.title("Configuration") # Moved title to sidebar
st.sidebar.header("General Settings")

config['ticker'] = st.sidebar.text_input("Ticker", value=config.get('ticker', 'AAPL'))
config['start_date'] = st.sidebar.date_input("Start Date", value=datetime.strptime(config.get('start_date', '2020-01-01'), '%Y-%m-%d')).strftime('%Y-%m-%d')
config['end_date'] = st.sidebar.date_input("End Date", value=datetime.strptime(config.get('end_date', '2023-01-01'), '%Y-%m-%d')).strftime('%Y-%m-%d')
config['period'] = st.sidebar.selectbox("Data Period", options=['1d', '1h', '15m'], index=['1d', '1h', '15m'].index(config.get('period')))
config['initial_capital'] = st.sidebar.number_input("Initial Capital", value=config.get('initial_capital', 10000.0), min_value=100.0, step=100.0)
config['fees_per_trade'] = st.sidebar.number_input("Fees per Trade", value=config.get('fees_per_trade', 0.0), min_value=0.0, step=0.01)


st.sidebar.header("Strategy Parameters")
# This part is strategy specific, for now we use the default from strategy.py
param_ranges = DEFAULT_PARAM_RANGES
params = {}
for name, p_range in param_ranges.items():
    # Use a unique key for each slider to prevent conflicts
    params[name] = st.sidebar.slider(name, min_value=p_range.start, max_value=p_range.stop -1, value=p_range.start, key=f"strategy_param_{name}")


st.sidebar.header("Optimization Settings")
config['enable_optimization'] = st.sidebar.checkbox("Enable Optimization", value=config.get('enable_optimization', False))
if config['enable_optimization']:
    config['epochs'] = st.sidebar.number_input("Epochs", value=config.get('epochs', 100), min_value=1, step=1)
    config['metric'] = st.sidebar.selectbox("Metric to Optimize", options=['pnl_pct_total', 'sortino', 'sharpe', 'max_drawdown'], index=['pnl_pct_total', 'sortino', 'sharpe', 'max_drawdown'].index(config.get('metric')), key="optimization_metric")


if st.sidebar.button("Save Configuration"):
    save_config(config)
    st.sidebar.success("Configuration saved!")

# Main panel
if st.button("Run Backtest"):
    st.info("Running backtest...")
    log_capture = StreamlitLogCapture()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = log_capture
    sys.stderr = log_capture
    
    try:
        with st.spinner('Fetching data and running backtest...'):
            df_result, metrics, trades_df_result, fig = backtest_strategy(
                ticker=config['ticker'],
                start_date=config['start_date'],
                end_date=config['end_date'],
                initial_capital=config['initial_capital'],
                fees_per_trade=config['fees_per_trade'], # Pass fees_per_trade
                params=params,
                show_plot=True
            )
        st.session_state.backtest_fig = fig
        st.session_state.backtest_metrics = metrics
        st.session_state.backtest_trades = trades_df_result # Store trades_df for display
        st.success("Backtest completed!")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        with st.expander("Show Backtest Logs"):
            st.code("\n".join(log_capture.log_messages))

if config['enable_optimization']:
    if st.button("Run Optimization"):
        st.info("Running optimization...")
        log_capture = StreamlitLogCapture()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = log_capture
        sys.stderr = log_capture
        try:
            with st.spinner('This might take a while...'):
                best_result, fig = run_optimization(
                    epochs=config['epochs'],
                    metric=config['metric'],
                    ticker=config['ticker'],
                    start_date=config['start_date'],
                    end_date=config['end_date'],
                    initial_capital=config['initial_capital']
                )
                if best_result:
                    st.session_state.backtest_fig = fig
                    st.session_state.backtest_metrics = best_result['metrics']
                    st.session_state.best_params = best_result['params'] # Store best params
                    st.session_state.is_optimized = True # Flag for optimized run
                    st.success("Optimization completed!")

                else:
                    st.error("Optimization failed to produce a result.")

        except Exception as e:
            st.error(f"An error occurred during optimization: {e}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            with st.expander("Show Optimization Logs"):
                st.code("\n".join(log_capture.log_messages))


# Display results
if 'backtest_fig' in st.session_state and st.session_state.backtest_fig:
    st.header("Backtest Results")

    # Display plot first
    st.pyplot(st.session_state.backtest_fig)

    if st.session_state.get('is_optimized', False):
        st.subheader("Best Parameters:")
        # Convert best_params dictionary to a DataFrame for elegant display
        best_params_df = pd.DataFrame(list(st.session_state.best_params.items()), columns=['Parameter', 'Value'])
        st.dataframe(best_params_df, width='stretch')

        st.subheader("Performance Metrics:")
    else:
        st.subheader("Performance Metrics:") # For regular backtest

    # Display metrics table
    formatted_metrics = format_summary(st.session_state.backtest_metrics, config['initial_capital'])
    metrics_df = format_metrics_dataframe(formatted_metrics)
    st.dataframe(metrics_df, width='stretch')

    # Display trade list table
    st.header("Trade List")
    # Check if backtest_trades exists before trying to format
    if 'backtest_trades' in st.session_state and st.session_state.backtest_trades is not None:
        trades_df_display = format_trades_list(st.session_state.backtest_trades)
        if not trades_df_display.empty:
            st.dataframe(trades_df_display, width='stretch')
        else:
            st.info("No trades executed.")
    else:
        st.info("No trade data available.")
