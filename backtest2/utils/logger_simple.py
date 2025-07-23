"""Simple logger for backtest system"""

import logging
from pathlib import Path
from typing import Any, Optional


class BacktestLogger:
    """Logger for backtest execution"""
    
    def __init__(self, result_dir: Optional[Path] = None):
        """Initialize logger
        
        Args:
            result_dir: Directory to save logs
        """
        self.logger = logging.getLogger("BacktestLogger")
        self.result_dir = result_dir
        
    async def save_results(self, result: Any) -> None:
        """Save backtest results
        
        Args:
            result: BacktestResult object
        """
        if self.result_dir:
            self.result_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Results saved to {self.result_dir}")
        
    def log_transaction(self, transaction: Any) -> None:
        """Log a transaction"""
        self.logger.info(f"Transaction: {transaction}")
        
    def log_decision(self, decision: Any) -> None:
        """Log a trading decision"""
        self.logger.debug(f"Decision: {decision}")