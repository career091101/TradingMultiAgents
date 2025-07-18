"""
Plotting utilities for backtest visualization.

This module provides functions to create various plots for analyzing
backtest results including equity curves, price charts with signals, etc.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os


def setup_plot_style():
    """Set up a clean plotting style."""
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['lines.linewidth'] = 2


def plot_equity_curve(dates: List[datetime], equity_values: List[float], 
                     title: str = "Portfolio Equity Curve",
                     save_path: Optional[str] = None) -> None:
    """
    Plot the equity curve showing portfolio value over time.
    
    Args:
        dates: List of dates
        equity_values: List of portfolio values
        title: Plot title
        save_path: Optional path to save the plot
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Convert to pandas series for easier plotting
    equity_series = pd.Series(equity_values, index=pd.to_datetime(dates))
    
    # Plot equity curve
    ax.plot(equity_series.index, equity_series.values, 'b-', linewidth=2, label='Portfolio Value')
    
    # Add initial value reference line
    initial_value = equity_values[0] if equity_values else 0
    ax.axhline(y=initial_value, color='gray', linestyle='--', alpha=0.7, label='Initial Value')
    
    # Calculate and plot drawdown periods
    running_max = pd.Series(equity_values).expanding().max()
    drawdown = (pd.Series(equity_values) - running_max) / running_max
    
    # Shade drawdown periods
    for i in range(1, len(drawdown)):
        if drawdown.iloc[i] < 0:
            ax.fill_between([dates[i-1], dates[i]], 
                          [equity_values[i-1], equity_values[i]], 
                          [running_max.iloc[i-1], running_max.iloc[i]], 
                          alpha=0.3, color='red')
    
    # Format axes
    ax.set_xlabel('Date')
    ax.set_ylabel('Portfolio Value ($)')
    ax.set_title(title)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add legend
    ax.legend(loc='best')
    
    # Add performance statistics
    total_return = ((equity_values[-1] - equity_values[0]) / equity_values[0] * 100) if equity_values else 0
    max_dd = drawdown.min() * 100
    
    stats_text = f'Total Return: {total_return:.2f}%\nMax Drawdown: {max_dd:.2f}%'
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            verticalalignment='top')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Equity curve saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_price_with_signals(result, ticker: str, 
                           save_path: Optional[str] = None) -> None:
    """
    Plot stock price with buy/sell signals marked.
    
    Args:
        result: BacktestResult object
        ticker: Stock ticker symbol
        save_path: Optional path to save the plot
    """
    setup_plot_style()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), 
                                   gridspec_kw={'height_ratios': [3, 1]})
    
    # Extract price data from trades
    dates = [trade.date for trade in result.trades]
    prices = [trade.price for trade in result.trades]
    
    # Create price series
    price_series = pd.Series(prices, index=pd.to_datetime(dates))
    
    # Plot price
    ax1.plot(price_series.index, price_series.values, 'k-', linewidth=1.5, label='Price')
    
    # Mark buy and sell signals
    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []
    
    for trade in result.trades:
        if trade.action == "BUY":
            buy_dates.append(trade.date)
            buy_prices.append(trade.price)
        elif trade.action == "SELL":
            sell_dates.append(trade.date)
            sell_prices.append(trade.price)
    
    # Plot buy signals
    if buy_dates:
        ax1.scatter(pd.to_datetime(buy_dates), buy_prices, 
                   color='green', marker='^', s=100, label='Buy', zorder=5)
    
    # Plot sell signals
    if sell_dates:
        ax1.scatter(pd.to_datetime(sell_dates), sell_prices, 
                   color='red', marker='v', s=100, label='Sell', zorder=5)
    
    # Format price chart
    ax1.set_ylabel('Price ($)')
    ax1.set_title(f'{ticker} Price with Trading Signals')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot position indicator
    position_indicator = []
    for i, trade in enumerate(result.trades):
        if trade.shares > 0:
            position_indicator.append(1)  # Long position
        else:
            position_indicator.append(0)  # No position
    
    position_series = pd.Series(position_indicator, index=pd.to_datetime(dates))
    ax2.fill_between(position_series.index, 0, position_series.values, 
                    alpha=0.3, color='green', label='Position')
    ax2.set_ylabel('Position')
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_xlabel('Date')
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis dates
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Price chart saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_drawdown(dates: List[datetime], equity_values: List[float],
                 save_path: Optional[str] = None) -> None:
    """
    Plot drawdown chart showing underwater periods.
    
    Args:
        dates: List of dates
        equity_values: List of portfolio values
        save_path: Optional path to save the plot
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Calculate drawdown
    equity_series = pd.Series(equity_values)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max * 100
    
    # Create drawdown series with dates
    dd_series = pd.Series(drawdown.values, index=pd.to_datetime(dates))
    
    # Plot drawdown
    ax.fill_between(dd_series.index, 0, dd_series.values, 
                   color='red', alpha=0.3, label='Drawdown')
    ax.plot(dd_series.index, dd_series.values, 'r-', linewidth=1)
    
    # Add zero line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Format axes
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.set_title('Portfolio Drawdown')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    # Add max drawdown annotation
    max_dd_idx = drawdown.idxmin()
    max_dd_value = drawdown.min()
    max_dd_date = dates[max_dd_idx]
    
    ax.annotate(f'Max DD: {max_dd_value:.2f}%',
                xy=(max_dd_date, max_dd_value),
                xytext=(max_dd_date, max_dd_value - 5),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10,
                color='red')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Drawdown chart saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_returns_distribution(result, save_path: Optional[str] = None) -> None:
    """
    Plot distribution of returns.
    
    Args:
        result: BacktestResult object
        save_path: Optional path to save the plot
    """
    setup_plot_style()
    
    # Calculate daily returns
    returns = []
    for i in range(1, len(result.equity_curve)):
        daily_return = ((result.equity_curve[i] - result.equity_curve[i-1]) / 
                       result.equity_curve[i-1] * 100)
        returns.append(daily_return)
    
    if not returns:
        print("Not enough data to plot returns distribution")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Histogram
    ax1.hist(returns, bins=30, alpha=0.7, color='blue', edgecolor='black')
    ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7)
    ax1.axvline(x=np.mean(returns), color='green', linestyle='--', 
                label=f'Mean: {np.mean(returns):.2f}%')
    ax1.set_xlabel('Daily Return (%)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Daily Returns')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Q-Q plot
    from scipy import stats
    stats.probplot(returns, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot (Normal Distribution)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Returns distribution saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def create_backtest_report(result, ticker: str, output_dir: str = "./backtest/results") -> None:
    """
    Create a complete visual report for the backtest.
    
    Args:
        result: BacktestResult object
        ticker: Stock ticker symbol
        output_dir: Directory to save the plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create all plots
    print(f"Generating backtest report for {ticker}...")
    
    # 1. Equity curve
    equity_path = os.path.join(output_dir, f"{ticker}_equity_curve_{timestamp}.png")
    plot_equity_curve(result.dates, result.equity_curve, 
                     title=f"{ticker} Portfolio Equity Curve", 
                     save_path=equity_path)
    
    # 2. Price with signals
    signals_path = os.path.join(output_dir, f"{ticker}_price_signals_{timestamp}.png")
    plot_price_with_signals(result, ticker, save_path=signals_path)
    
    # 3. Drawdown chart
    drawdown_path = os.path.join(output_dir, f"{ticker}_drawdown_{timestamp}.png")
    plot_drawdown(result.dates, result.equity_curve, save_path=drawdown_path)
    
    # 4. Returns distribution
    returns_path = os.path.join(output_dir, f"{ticker}_returns_dist_{timestamp}.png")
    plot_returns_distribution(result, save_path=returns_path)
    
    print(f"Backtest report saved to: {output_dir}")
    
    return {
        'equity_curve': equity_path,
        'price_signals': signals_path,
        'drawdown': drawdown_path,
        'returns_distribution': returns_path
    }