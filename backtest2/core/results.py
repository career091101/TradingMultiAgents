"""Backtest results container and analysis"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

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
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary"""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'final_value': self.final_value,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'beta': self.beta
        }


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
    daily_returns: Optional[pd.Series] = None
    equity_curve: Optional[pd.Series] = None
    position_history: Optional[pd.DataFrame] = None
    
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
        
        if self.metrics.benchmark_return is not None:
            summary += f"""
Benchmark Comparison
-------------------
Benchmark Return: {self.metrics.benchmark_return:.2%}
Alpha: {self.metrics.alpha:.2%}
Beta: {self.metrics.beta:.2f}
"""
        
        return summary
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame for analysis"""
        # Create transaction dataframe
        if self.transactions:
            df = pd.DataFrame([
                {
                    'timestamp': t.timestamp,
                    'symbol': t.symbol,
                    'action': t.action.value,
                    'quantity': t.quantity,
                    'price': t.price,
                    'commission': t.commission,
                    'total_cost': t.total_cost
                }
                for t in self.transactions
            ])
            df.set_index('timestamp', inplace=True)
            return df
        return pd.DataFrame()
    
    def get_monthly_returns(self) -> pd.Series:
        """Calculate monthly returns"""
        if self.daily_returns is None:
            return pd.Series()
            
        monthly = self.daily_returns.resample('M').apply(
            lambda x: (1 + x).prod() - 1
        )
        return monthly
    
    def get_trade_analysis(self) -> pd.DataFrame:
        """Analyze trades by various dimensions"""
        if not self.transactions:
            return pd.DataFrame()
            
        trades_df = []
        current_position = {}
        
        for t in self.transactions:
            if t.action.value == 'BUY':
                current_position[t.symbol] = {
                    'entry_date': t.timestamp,
                    'entry_price': t.price,
                    'quantity': t.quantity
                }
            elif t.action.value == 'SELL' and t.symbol in current_position:
                entry = current_position[t.symbol]
                trades_df.append({
                    'symbol': t.symbol,
                    'entry_date': entry['entry_date'],
                    'exit_date': t.timestamp,
                    'entry_price': entry['entry_price'],
                    'exit_price': t.price,
                    'quantity': entry['quantity'],
                    'holding_days': (t.timestamp - entry['entry_date']).days,
                    'return': (t.price - entry['entry_price']) / entry['entry_price'],
                    'pnl': (t.price - entry['entry_price']) * entry['quantity']
                })
                del current_position[t.symbol]
                
        return pd.DataFrame(trades_df)
    
    def save_to_csv(self, filepath: str) -> None:
        """Save results to CSV files"""
        import os
        
        # Create directory if needed
        os.makedirs(filepath, exist_ok=True)
        
        # Save metrics
        metrics_df = pd.DataFrame([self.metrics.to_dict()])
        metrics_df.to_csv(f"{filepath}/metrics.csv", index=False)
        
        # Save transactions
        if self.transactions:
            self.to_dataframe().to_csv(f"{filepath}/transactions.csv")
            
        # Save trade analysis
        trade_analysis = self.get_trade_analysis()
        if not trade_analysis.empty:
            trade_analysis.to_csv(f"{filepath}/trade_analysis.csv", index=False)
            
        # Save equity curve
        if self.equity_curve is not None:
            self.equity_curve.to_csv(f"{filepath}/equity_curve.csv")
            
        # Save summary
        with open(f"{filepath}/summary.txt", 'w') as f:
            f.write(self.get_summary())