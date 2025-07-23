"""Logging utilities for backtest"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict
import aiofiles

from ..core.results import BacktestResult


class BacktestLogger:
    """Handles logging and result saving"""
    
    def __init__(self, results_path: str = "./results"):
        self.results_path = results_path
        self.logger = logging.getLogger(__name__)
        
        # Create results directory
        os.makedirs(results_path, exist_ok=True)
        
    async def save_results(self, result: BacktestResult) -> None:
        """Save backtest results"""
        # Create subdirectory for this run
        run_dir = os.path.join(
            self.results_path,
            f"backtest_{result.execution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(run_dir, exist_ok=True)
        
        # Save summary
        summary_path = os.path.join(run_dir, "summary.txt")
        async with aiofiles.open(summary_path, 'w') as f:
            await f.write(result.get_summary())
            
        # Save metrics as JSON
        metrics_path = os.path.join(run_dir, "metrics.json")
        async with aiofiles.open(metrics_path, 'w') as f:
            metrics_dict = {
                'execution_id': result.execution_id,
                'start_date': result.config.start_date.isoformat(),
                'end_date': result.config.end_date.isoformat(),
                'initial_capital': result.config.initial_capital,
                'symbols': result.config.symbols,
                'metrics': {
                    'total_return': result.metrics.total_return,
                    'annualized_return': result.metrics.annualized_return,
                    'sharpe_ratio': result.metrics.sharpe_ratio,
                    'max_drawdown': result.metrics.max_drawdown,
                    'win_rate': result.metrics.win_rate,
                    'total_trades': result.metrics.total_trades
                }
            }
            await f.write(json.dumps(metrics_dict, indent=2))
            
        # Save transactions
        if result.transactions:
            transactions_path = os.path.join(run_dir, "transactions.json")
            async with aiofiles.open(transactions_path, 'w') as f:
                tx_list = [
                    {
                        'timestamp': tx.timestamp.isoformat(),
                        'symbol': tx.symbol,
                        'action': tx.action.value,
                        'quantity': tx.quantity,
                        'price': tx.price,
                        'commission': tx.commission,
                        'total_cost': tx.total_cost
                    }
                    for tx in result.transactions
                ]
                await f.write(json.dumps(tx_list, indent=2))
                
        self.logger.info(f"Results saved to {run_dir}")
        
    def log_progress(self, message: str, progress: float = None) -> None:
        """Log progress message"""
        if progress is not None:
            self.logger.info(f"[{progress:.1%}] {message}")
        else:
            self.logger.info(message)