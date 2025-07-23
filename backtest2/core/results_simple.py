"""Simplified results container without pandas dependency"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .config import BacktestConfig
from .types import Transaction, PortfolioState


@dataclass
class PerformanceMetrics:
    """Performance metrics for backtest results"""
    # Return metrics
    total_return: float
    annualized_return: float
    
    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int  # days
    
    # Trading metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    
    # Portfolio metrics
    final_value: float
    peak_value: float
    lowest_value: float
    
    # Benchmark comparison
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    
    # Additional metrics
    calmar_ratio: Optional[float] = None
    var_95: Optional[float] = None  # Value at Risk
    cvar_95: Optional[float] = None  # Conditional VaR


@dataclass  
class BacktestResult:
    """Complete backtest results"""
    execution_id: str
    config: BacktestConfig
    metrics: PerformanceMetrics
    transactions: List[Transaction]
    final_portfolio: PortfolioState
    
    # Additional analysis
    agent_performance: Dict[str, Any] = field(default_factory=dict)
    benchmark_comparison: Optional[Dict[str, Dict[str, float]]] = None
    benchmark_report: Optional[str] = None
    
    # Execution metadata
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    
    def get_summary(self) -> str:
        """Get a text summary of results"""
        summary = f"""
Backtest Results Summary
========================
Execution ID: {self.execution_id}
Period: {self.config.start_date.date()} to {self.config.end_date.date()}
Initial Capital: ${self.config.initial_capital:,.2f}
Final Value: ${self.metrics.final_value:,.2f}

Performance Metrics
------------------
Total Return: {self.metrics.total_return:.2%}
Annualized Return: {self.metrics.annualized_return:.2%}
Volatility: {self.metrics.volatility:.2%}
Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}
Max Drawdown: {self.metrics.max_drawdown:.2%}

Trading Statistics
-----------------
Total Trades: {self.metrics.total_trades}
Win Rate: {self.metrics.win_rate:.2%}
Profit Factor: {self.metrics.profit_factor:.2f}
Average Win: ${self.metrics.average_win:,.2f}
Average Loss: ${self.metrics.average_loss:,.2f}
"""
        
        if self.benchmark_comparison:
            benchmark = self.benchmark_comparison.get('benchmark', {})
            relative = self.benchmark_comparison.get('relative', {})
            summary += f"""
Benchmark Comparison
-------------------
Benchmark Return: {benchmark.get('total_return', 0):.2%}
Alpha: {relative.get('alpha', 0):.2%}
Beta: {relative.get('beta', 1):.2f}
Outperformance: {relative.get('outperformance', 0):.2%}
"""
        
        return summary