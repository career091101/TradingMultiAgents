#!/usr/bin/env python3
"""
Example usage of the TradingAgents backtesting framework.

This script demonstrates how to use the backtesting module programmatically.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.simulator import BacktestSimulator
from backtest.metrics import calculate_performance_metrics, format_metrics_report
from backtest.plotting import create_backtest_report


def example_simple_backtest():
    """Example: Simple backtest for a single stock."""
    print("=" * 60)
    print("Example 1: Simple Single Stock Backtest")
    print("=" * 60)
    
    # Initialize simulator with default config
    simulator = BacktestSimulator(debug=False)
    
    # Run backtest for Apple stock
    result = simulator.run_backtest(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=10000.0,
        slippage=0.001  # 0.1% slippage
    )
    
    # Calculate and display metrics
    metrics = calculate_performance_metrics(result)
    print(format_metrics_report(metrics, "AAPL"))
    
    # Generate plots
    create_backtest_report(result, "AAPL", "./backtest/results/example1")
    
    return result, metrics


def example_custom_config_backtest():
    """Example: Backtest with custom TradingAgents configuration."""
    print("\n" + "=" * 60)
    print("Example 2: Backtest with Custom Configuration")
    print("=" * 60)
    
    # Custom configuration
    custom_config = {
        "llm_provider": "openai",
        "quick_think_llm": "gpt-4o-mini",
        "deep_think_llm": "o4-mini-2025-04-16",
        "max_debate_rounds": 2,
        "max_risk_discuss_rounds": 2,
        "online_tools": False  # Use offline data for reproducibility
    }
    
    # Initialize simulator with custom config
    simulator = BacktestSimulator(config=custom_config, debug=True)
    
    # Run backtest
    result = simulator.run_backtest(
        ticker="MSFT",
        start_date="2023-06-01",
        end_date="2023-12-31",
        initial_capital=25000.0,
        slippage=0.002  # 0.2% slippage
    )
    
    # Calculate metrics with custom risk-free rate
    metrics = calculate_performance_metrics(result, risk_free_rate=0.05)
    print(format_metrics_report(metrics, "MSFT"))
    
    return result, metrics


def example_portfolio_backtest():
    """Example: Portfolio backtest with multiple stocks."""
    print("\n" + "=" * 60)
    print("Example 3: Portfolio Backtest")
    print("=" * 60)
    
    # Initialize simulator
    simulator = BacktestSimulator(debug=False)
    
    # Define portfolio
    portfolio_tickers = ["AAPL", "MSFT", "GOOGL"]
    total_capital = 30000.0
    
    # Run backtests for each ticker
    results = simulator.run_portfolio_backtest(
        tickers=portfolio_tickers,
        start_date="2023-01-01",
        end_date="2023-06-30",
        initial_capital=total_capital,
        slippage=0.001
    )
    
    # Display results for each ticker
    total_final_value = 0
    for ticker, result in results.items():
        metrics = calculate_performance_metrics(result)
        print(f"\n{ticker} Performance:")
        print(f"  Total Return: {metrics.total_return:.2f}%")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {metrics.max_drawdown:.2f}%")
        print(f"  Win Rate: {metrics.win_rate:.2f}%")
        total_final_value += result.final_portfolio_value
    
    # Portfolio summary
    portfolio_return = ((total_final_value - total_capital) / total_capital) * 100
    print(f"\nPortfolio Summary:")
    print(f"  Initial Capital: ${total_capital:,.2f}")
    print(f"  Final Value: ${total_final_value:,.2f}")
    print(f"  Total Return: {portfolio_return:.2f}%")
    
    return results


def example_analyze_trades():
    """Example: Detailed analysis of individual trades."""
    print("\n" + "=" * 60)
    print("Example 4: Detailed Trade Analysis")
    print("=" * 60)
    
    # Run a backtest
    simulator = BacktestSimulator(debug=False)
    result = simulator.run_backtest(
        ticker="TSLA",
        start_date="2023-01-01",
        end_date="2023-03-31",
        initial_capital=50000.0,
        slippage=0.001
    )
    
    # Analyze trades
    print(f"\nTotal trades executed: {len(result.trades)}")
    
    # Show first 10 trades
    print("\nFirst 10 trades:")
    print(f"{'Date':<12} {'Action':<6} {'Price':>10} {'Shares':>10} {'Portfolio':>12}")
    print("-" * 55)
    
    for trade in result.trades[:10]:
        print(f"{trade.date.strftime('%Y-%m-%d'):<12} "
              f"{trade.action:<6} "
              f"${trade.price:>9.2f} "
              f"{trade.shares:>10.2f} "
              f"${trade.portfolio_value:>11,.2f}")
    
    # Find best and worst performing trades
    buy_sell_pairs = []
    buy_trade = None
    
    for trade in result.trades:
        if trade.action == "BUY":
            buy_trade = trade
        elif trade.action == "SELL" and buy_trade:
            return_pct = ((trade.price - buy_trade.price) / buy_trade.price) * 100
            buy_sell_pairs.append({
                'buy_date': buy_trade.date,
                'sell_date': trade.date,
                'buy_price': buy_trade.price,
                'sell_price': trade.price,
                'return_pct': return_pct
            })
            buy_trade = None
    
    if buy_sell_pairs:
        # Sort by return
        buy_sell_pairs.sort(key=lambda x: x['return_pct'], reverse=True)
        
        print(f"\nBest trade:")
        best = buy_sell_pairs[0]
        print(f"  Buy: {best['buy_date'].strftime('%Y-%m-%d')} @ ${best['buy_price']:.2f}")
        print(f"  Sell: {best['sell_date'].strftime('%Y-%m-%d')} @ ${best['sell_price']:.2f}")
        print(f"  Return: {best['return_pct']:.2f}%")
        
        print(f"\nWorst trade:")
        worst = buy_sell_pairs[-1]
        print(f"  Buy: {worst['buy_date'].strftime('%Y-%m-%d')} @ ${worst['buy_price']:.2f}")
        print(f"  Sell: {worst['sell_date'].strftime('%Y-%m-%d')} @ ${worst['sell_price']:.2f}")
        print(f"  Return: {worst['return_pct']:.2f}%")
    
    return result


def main():
    """Run all examples."""
    print("TradingAgents Backtesting Framework - Examples")
    print("=" * 60)
    
    # Create results directory
    os.makedirs("./backtest/results", exist_ok=True)
    
    try:
        # Run examples
        # Note: These examples require proper API keys to be set up
        # for the TradingAgents framework to work
        
        # Example 1: Simple backtest
        result1, metrics1 = example_simple_backtest()
        
        # Example 2: Custom configuration
        # result2, metrics2 = example_custom_config_backtest()
        
        # Example 3: Portfolio backtest
        # portfolio_results = example_portfolio_backtest()
        
        # Example 4: Trade analysis
        # trade_analysis_result = example_analyze_trades()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("Results saved in ./backtest/results/")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure you have:")
        print("1. Set up the TradingAgents framework properly")
        print("2. Configured API keys (OpenAI, etc.)")
        print("3. Installed all required dependencies")


if __name__ == "__main__":
    main()