# optimizer module for parameter optimization
import itertools
from tqdm import tqdm
import optuna

# Default configuration
DEFAULT_EPOCHS = 100
DEFAULT_METRIC = 'pnl_pct_total'

def _objective(trial, param_ranges, metric, backtest_kwargs):
    """
    Objective function for Optuna optimization.
    """
    from backtesting import backtest_strategy

    params = {}
    for name, range_ in param_ranges.items():
        if isinstance(range_, range):
            params[name] = trial.suggest_int(name, range_.start, range_.stop - 1, range_.step)
        elif isinstance(range_, list):
            params[name] = trial.suggest_categorical(name, range_)
        # Add more types if needed, e.g., float
        # elif isinstance(param_ranges[name], tuple) and len(param_ranges[name]) == 2:
        #     params[name] = trial.suggest_float(name, param_ranges[name][0], param_ranges[name][1])

    if 'fast_length' in params and 'slow_length' in params:
        if params['fast_length'] >= params['slow_length']:
            raise optuna.exceptions.TrialPruned()

    try:
        _, metrics, _, _ = backtest_strategy(params=params, show_plot=False, **backtest_kwargs)
        return metrics.get(metric, 0.0)
    except Exception as e:
        tqdm.write(f"Error with params {params}: {e}")
        return float('-inf') # Indicate failure


def optimize_parameters(epochs: int,
                        param_ranges: dict,
                        metric: str = 'sortino',
                        **backtest_kwargs) -> tuple:
    """
    Optimize strategy parameters using Optuna.

    Args:
        epochs (int): Number of trials to run.
        param_ranges (dict): Dictionary of parameter names to ranges (e.g., {'fast_length': range(5,15)}).
        metric (str): Metric to optimize for ('sortino', 'sharpe', 'pnl_pct_total', 'max_drawdown', etc.).
        **backtest_kwargs: Additional arguments for backtest_strategy.

    Returns:
        tuple: (best_result, all_results) where each result is {'params': dict, 'metrics': dict}
    """
    from backtesting import backtest_strategy

    direction = 'minimize' if metric == 'max_drawdown' else 'maximize'
    study = optuna.create_study(direction=direction)
    
    objective_func = lambda trial: _objective(trial, param_ranges, metric, backtest_kwargs)
    
    study.optimize(objective_func, n_trials=epochs, callbacks=[lambda study, trial: tqdm.write(f"Trial {trial.number} finished with value: {trial.value}")])

    best_params = study.best_params
    
    # Rerun with best params to get full metrics
    _, best_metrics, _, _ = backtest_strategy(params=best_params, show_plot=False, **backtest_kwargs)
    
    best_result = {'params': best_params, 'metrics': best_metrics}

    # Optuna doesn't easily expose all trial results with metrics in the format we want.
    # We can fetch them if needed, but for now we return the best result and an empty list for all_results
    # to maintain the same function signature.
    all_results = []
    
    return best_result, all_results


def run_optimization(epochs=None, param_ranges=None, metric=None, **backtest_kwargs):
    """
    Run the full optimization process and return the best results and plot.

    Args:
        epochs (int, optional): Number of combinations to test. Defaults to DEFAULT_EPOCHS.
        param_ranges (dict, optional): Parameter ranges. Defaults to strategy.DEFAULT_PARAM_RANGES.
        metric (str, optional): Metric to optimize. Defaults to DEFAULT_METRIC.
        **backtest_kwargs: Additional arguments for backtest_strategy.
        
    Returns:
        tuple: (best_result, figure)
    """
    if epochs is None:
        epochs = DEFAULT_EPOCHS
    if param_ranges is None:
        from strategy import DEFAULT_PARAM_RANGES
        param_ranges = DEFAULT_PARAM_RANGES
    if metric is None:
        metric = DEFAULT_METRIC

    best, all_results = optimize_parameters(epochs, param_ranges, metric, **backtest_kwargs)

    if best:
        # Run the best backtest with plot
        from backtesting import backtest_strategy
        _, metrics, _, fig = backtest_strategy(params=best['params'], show_plot=True, **backtest_kwargs)
        best['metrics'] = metrics # update metrics from the final run
        return best, fig
    else:
        return None, None
