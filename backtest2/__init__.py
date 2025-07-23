"""
TradingAgents2 Backtest Module
Advanced backtesting framework with multi-agent coordination and learning capabilities
"""

__version__ = "2.0.0"
__author__ = "TradingAgents2 Team"

from .core.config import BacktestConfig
from .core.results_simple import BacktestResult
from .core.engine import BacktestEngine

__all__ = [
    "BacktestEngine",
    "BacktestConfig", 
    "BacktestResult"
]