"""
Performance metrics calculation for backtesting results.

This module provides functions to calculate various performance metrics
such as Sharpe ratio, maximum drawdown, win rate, etc.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics."""
    total_return: float  # Percentage
    annualized_return: float  # Percentage
    max_drawdown: float  # Percentage
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float  # Percentage
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float  # Percentage
    avg_loss: float  # Percentage
    profit_factor: float
    calmar_ratio: float
    volatility: float  # Annualized


def calculate_returns(equity_curve: List[float]) -> np.ndarray:
    """
    Calculate daily returns from equity curve.
    
    Args:
        equity_curve: List of portfolio values over time
        
    Returns:
        Array of daily returns
    """
    if len(equity_curve) < 2:
        return np.array([])
    
    equity_array = np.array(equity_curve)
    returns = np.diff(equity_array) / equity_array[:-1]
    
    return returns


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
    """
    Calculate maximum drawdown and its duration.
    
    Args:
        equity_curve: List of portfolio values over time
        
    Returns:
        Tuple of (max_drawdown_percentage, peak_idx, trough_idx)
    """
    if len(equity_curve) < 2:
        return 0.0, 0, 0
    
    equity_array = np.array(equity_curve)
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_array)
    
    # Calculate drawdown at each point
    drawdown = (equity_array - running_max) / running_max
    
    # Find maximum drawdown
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]
    
    # Find the peak before the maximum drawdown
    peak_idx = np.where(equity_array[:max_dd_idx+1] == running_max[max_dd_idx])[0][-1]
    
    return -max_dd * 100, peak_idx, max_dd_idx


def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02, 
                          periods_per_year: int = 252) -> float:
    """
    Calculate the Sharpe ratio.
    
    Args:
        returns: Array of returns
        risk_free_rate: Annual risk-free rate (default: 2%)
        periods_per_year: Number of trading periods per year (default: 252 for daily)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Convert annual risk-free rate to period rate
    period_risk_free = risk_free_rate / periods_per_year
    
    # Calculate excess returns
    excess_returns = returns - period_risk_free
    
    # Calculate Sharpe ratio
    if np.std(excess_returns) == 0:
        return 0.0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)
    
    return sharpe


def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02,
                           periods_per_year: int = 252) -> float:
    """
    Calculate the Sortino ratio (uses downside deviation).
    
    Args:
        returns: Array of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of trading periods per year
        
    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Convert annual risk-free rate to period rate
    period_risk_free = risk_free_rate / periods_per_year
    
    # Calculate excess returns
    excess_returns = returns - period_risk_free
    
    # Calculate downside returns (only negative excess returns)
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        return float('inf')  # No downside risk
    
    # Calculate downside deviation
    downside_std = np.std(downside_returns)
    
    if downside_std == 0:
        return 0.0
    
    sortino = np.mean(excess_returns) / downside_std * np.sqrt(periods_per_year)
    
    return sortino


def analyze_trades(trades: List) -> Dict[str, float]:
    """
    Analyze individual trades to calculate win rate, average win/loss, etc.
    
    Args:
        trades: List of Trade objects
        
    Returns:
        Dictionary with trade analysis metrics
    """
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }
    
    # Extract buy and sell trades
    buy_trades = []
    sell_trades = []
    
    for trade in trades:
        if trade.action == "BUY":
            buy_trades.append(trade)
        elif trade.action == "SELL":
            sell_trades.append(trade)
    
    # Match buy and sell trades to calculate returns
    trade_returns = []
    
    for i, sell in enumerate(sell_trades):
        # Find the most recent buy before this sell
        recent_buy = None
        for buy in reversed(buy_trades):
            if buy.date < sell.date:
                recent_buy = buy
                break
        
        if recent_buy:
            # Calculate return percentage
            return_pct = ((sell.price - recent_buy.price) / recent_buy.price) * 100
            trade_returns.append(return_pct)
    
    if not trade_returns:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }
    
    # Calculate metrics
    trade_returns_array = np.array(trade_returns)
    winning_trades = trade_returns_array[trade_returns_array > 0]
    losing_trades = trade_returns_array[trade_returns_array < 0]
    
    total_trades = len(trade_returns)
    num_winning = len(winning_trades)
    num_losing = len(losing_trades)
    
    win_rate = (num_winning / total_trades * 100) if total_trades > 0 else 0.0
    avg_win = np.mean(winning_trades) if num_winning > 0 else 0.0
    avg_loss = np.mean(losing_trades) if num_losing > 0 else 0.0
    
    # Calculate profit factor
    total_wins = np.sum(winning_trades) if num_winning > 0 else 0.0
    total_losses = abs(np.sum(losing_trades)) if num_losing > 0 else 1.0
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'winning_trades': num_winning,
        'losing_trades': num_losing,
        'avg_win': avg_win,
        'avg_loss': abs(avg_loss),
        'profit_factor': profit_factor
    }


def calculate_performance_metrics(result, risk_free_rate: float = 0.02) -> PerformanceMetrics:
    """
    Calculate all performance metrics for a backtest result.
    
    Args:
        result: BacktestResult object
        risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
        
    Returns:
        PerformanceMetrics object with all calculated metrics
    """
    # Basic return calculation
    total_return = result.total_return
    
    # Calculate daily returns
    returns = calculate_returns(result.equity_curve)
    
    # Calculate annualized return
    if len(result.dates) > 1:
        days = (result.dates[-1] - result.dates[0]).days
        years = days / 365.25
        annualized_return = ((result.final_portfolio_value / result.initial_capital) ** (1/years) - 1) * 100
    else:
        annualized_return = 0.0
    
    # Calculate maximum drawdown
    max_dd, _, _ = calculate_max_drawdown(result.equity_curve)
    
    # Calculate Sharpe and Sortino ratios
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
    sortino = calculate_sortino_ratio(returns, risk_free_rate)
    
    # Analyze trades
    trade_analysis = analyze_trades(result.trades)
    
    # Calculate volatility (annualized)
    if len(returns) > 0:
        volatility = np.std(returns) * np.sqrt(252) * 100
    else:
        volatility = 0.0
    
    # Calculate Calmar ratio (annualized return / max drawdown)
    calmar = annualized_return / max_dd if max_dd > 0 else 0.0
    
    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        win_rate=trade_analysis['win_rate'],
        total_trades=trade_analysis['total_trades'],
        winning_trades=trade_analysis['winning_trades'],
        losing_trades=trade_analysis['losing_trades'],
        avg_win=trade_analysis['avg_win'],
        avg_loss=trade_analysis['avg_loss'],
        profit_factor=trade_analysis['profit_factor'],
        calmar_ratio=calmar,
        volatility=volatility
    )


def format_metrics_report(metrics: PerformanceMetrics, ticker: str = "") -> str:
    """
    Format performance metrics into a readable report.
    
    Args:
        metrics: PerformanceMetrics object
        ticker: Optional ticker symbol for the report header
        
    Returns:
        Formatted string report
    """
    header = f"Performance Report for {ticker}" if ticker else "Performance Report"
    separator = "=" * 50
    
    report = f"""
{header}
{separator}

Returns:
  Total Return:        {metrics.total_return:>10.2f}%
  Annualized Return:   {metrics.annualized_return:>10.2f}%
  
Risk Metrics:
  Maximum Drawdown:    {metrics.max_drawdown:>10.2f}%
  Volatility (Annual): {metrics.volatility:>10.2f}%
  
Risk-Adjusted Returns:
  Sharpe Ratio:        {metrics.sharpe_ratio:>10.2f}
  Sortino Ratio:       {metrics.sortino_ratio:>10.2f}
  Calmar Ratio:        {metrics.calmar_ratio:>10.2f}
  
Trading Statistics:
  Total Trades:        {metrics.total_trades:>10d}
  Win Rate:            {metrics.win_rate:>10.2f}%
  Winning Trades:      {metrics.winning_trades:>10d}
  Losing Trades:       {metrics.losing_trades:>10d}
  
Trade Performance:
  Average Win:         {metrics.avg_win:>10.2f}%
  Average Loss:        {metrics.avg_loss:>10.2f}%
  Profit Factor:       {metrics.profit_factor:>10.2f}

{separator}
"""
    
    return report