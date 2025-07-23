"""Simplified metrics calculator without numpy/pandas"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MetricsCalculator:
    """Simple metrics calculator for backtesting"""
    
    def __init__(self):
        """Initialize metrics calculator"""
        pass
        
    def calculate_daily_metrics(
        self,
        portfolio_state: Any,
        transactions: List[Any]
    ) -> Dict[str, float]:
        """Calculate daily metrics"""
        return {
            "daily_return": 0.0,
            "daily_trades": len(transactions),
            "portfolio_value": portfolio_state.total_value if portfolio_state else 0
        }
        
    def calculate_full_metrics(
        self,
        transactions: List[Any],
        portfolio_history: List[Any],
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate full backtest metrics"""
        # This is handled in BacktestResult now
        return {}