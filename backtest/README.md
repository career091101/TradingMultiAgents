# TradingAgents Backtesting Framework

This module provides comprehensive backtesting functionality for the TradingAgents framework, allowing you to evaluate trading strategies using historical data.

## Features

- **Historical Simulation**: Test your TradingAgents strategies on past market data
- **Performance Metrics**: Calculate key metrics including Sharpe ratio, maximum drawdown, win rate, etc.
- **Visualization**: Generate charts for equity curves, trading signals, drawdowns, and return distributions
- **Flexible Configuration**: Support for custom TradingAgents configurations and parameters
- **Portfolio Support**: Run backtests on multiple tickers with capital allocation
- **Trade Analysis**: Detailed logging and analysis of individual trades

## Installation

The backtesting module is included with TradingAgents. Ensure you have all dependencies installed:

```bash
pip install yfinance matplotlib pandas numpy scipy
```

## Quick Start

### Command Line Usage

Run a simple backtest from the command line:

```bash
python backtest/runner.py AAPL --start 2023-01-01 --end 2023-12-31 --capital 10000
```

Multiple tickers:

```bash
python backtest/runner.py AAPL MSFT GOOGL --start 2023-01-01 --end 2023-12-31 --capital 30000
```

### Programmatic Usage

```python
from backtest.simulator import BacktestSimulator
from backtest.metrics import calculate_performance_metrics

# Initialize simulator
simulator = BacktestSimulator()

# Run backtest
result = simulator.run_backtest(
    ticker="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=10000.0,
    slippage=0.001  # 0.1%
)

# Calculate metrics
metrics = calculate_performance_metrics(result)
print(f"Total Return: {metrics.total_return:.2f}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
```

## Command Line Options

```
usage: runner.py [-h] --start START --end END [--capital CAPITAL] 
                 [--slippage SLIPPAGE] [--config CONFIG] [--output OUTPUT]
                 [--no-plots] [--save-trades] [--debug] 
                 [--risk-free-rate RISK_FREE_RATE]
                 tickers [tickers ...]

Required Arguments:
  tickers              Stock ticker symbol(s) to backtest
  --start, -s          Start date (YYYY-MM-DD)
  --end, -e            End date (YYYY-MM-DD)

Optional Arguments:
  --capital, -c        Initial capital (default: $10,000)
  --slippage           Slippage percentage (default: 0.0)
  --config             Path to custom config JSON
  --output, -o         Output directory (default: ./backtest/results)
  --no-plots           Skip generating plots
  --save-trades        Save detailed trade log to CSV
  --debug              Enable debug mode
  --risk-free-rate     Risk-free rate for Sharpe calculation (default: 0.02)
```

## Performance Metrics

The framework calculates the following metrics:

- **Total Return**: Overall percentage gain/loss
- **Annualized Return**: Return normalized to yearly basis
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return metric
- **Sortino Ratio**: Downside risk-adjusted return
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Calmar Ratio**: Return to maximum drawdown ratio
- **Volatility**: Annualized standard deviation of returns

## Output Files

The backtest generates several output files:

1. **Metrics JSON**: Machine-readable performance metrics
2. **Trade Log CSV**: Detailed record of all trades (optional)
3. **Equity Curve Plot**: Portfolio value over time
4. **Price & Signals Plot**: Stock price with buy/sell markers
5. **Drawdown Chart**: Underwater periods visualization
6. **Returns Distribution**: Histogram and Q-Q plot of returns

## Custom Configuration

Create a custom config JSON for TradingAgents:

```json
{
    "llm_provider": "openai",
    "quick_think_llm": "gpt-4o-mini",
    "deep_think_llm": "o4-mini-2025-04-16",
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 2,
    "online_tools": false
}
```

Use with:

```bash
python backtest/runner.py AAPL --start 2023-01-01 --end 2023-12-31 --config myconfig.json
```

## Examples

See `example_usage.py` for detailed examples including:

1. Simple single stock backtest
2. Custom configuration backtest
3. Portfolio backtest with multiple stocks
4. Detailed trade analysis

Run examples:

```bash
python backtest/example_usage.py
```

## Important Notes

1. **API Keys**: Ensure TradingAgents is properly configured with necessary API keys
2. **Data Availability**: Historical data is fetched from Yahoo Finance
3. **Reproducibility**: Use `online_tools: false` in config for consistent results
4. **Performance**: Backtests can be slow due to LLM API calls for each trading day

## Limitations

- No support for short selling (initial implementation)
- Simple position sizing (all-in/all-out)
- No intraday trading (daily decisions only)
- Transaction costs limited to slippage (no commission modeling yet)

## Future Enhancements

- Short selling support
- Advanced position sizing strategies
- Intraday backtesting capability
- Commission and tax modeling
- Multi-asset portfolio optimization
- Walk-forward analysis
- Monte Carlo simulations