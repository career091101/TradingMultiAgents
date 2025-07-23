"""
Backtest wrapper for integrating the backtesting framework with the WebUI.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
import traceback

# Initialize logger first
logger = logging.getLogger(__name__)

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
backtest_path = os.path.join(project_root, 'backtest')

# Add both project root and backtest directory to path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backtest_path not in sys.path:
    sys.path.insert(0, backtest_path)

try:
    from backtest.simulator import BacktestSimulator
    from backtest.metrics import calculate_performance_metrics, format_metrics_report
    from backtest.plotting import create_backtest_report
except ImportError as e:
    # Try direct import from backtest directory
    try:
        from simulator import BacktestSimulator
        from metrics import calculate_performance_metrics, format_metrics_report
        from plotting import create_backtest_report
    except ImportError:
        logger.error(f"Failed to import backtest modules: {e}")
        logger.error(f"sys.path: {sys.path}")
        logger.error(f"Current directory: {os.getcwd()}")
        raise


class BacktestWrapper:
    """Wrapper class for running backtests from the WebUI."""
    
    def __init__(self):
        self.simulator = None
        self.is_running = False
        self.should_stop = False
        
    def run_backtest(self, config: Dict[str, Any], 
                    progress_callback: Optional[Callable] = None,
                    log_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run backtest with the given configuration.
        
        Args:
            config: Backtest configuration dictionary
            progress_callback: Function to call with progress updates (progress, status, ticker)
            log_callback: Function to call with log messages
            
        Returns:
            Dictionary of results for each ticker
        """
        self.is_running = True
        self.should_stop = False
        results = {}
        
        try:
            # Extract configuration
            tickers = config.get("tickers", ["AAPL"])
            start_date = config.get("start_date", "2023-01-01")
            end_date = config.get("end_date", "2023-12-31")
            initial_capital = config.get("initial_capital", 10000.0)
            slippage = config.get("slippage", 0.0)
            risk_free_rate = config.get("risk_free_rate", 0.02)
            save_trades = config.get("save_trades", True)
            generate_plots = config.get("generate_plots", True)
            debug = config.get("debug", False)
            
            # Agent configuration
            agent_config = config.get("agent_config", None)
            
            # Log start
            if log_callback:
                log_callback(f"Starting backtest for {len(tickers)} ticker(s)")
                log_callback(f"Period: {start_date} to {end_date}")
                log_callback(f"Initial capital per ticker: ${initial_capital / len(tickers):,.2f}")
            
            # Initialize simulator
            if progress_callback:
                progress_callback(0.0, "Initializing simulator...", "")
            
            # Prepare safe config for backtesting
            safe_config = {
                "project_dir": os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "results_dir": "./backtest/results",
                "data_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data"),
                "data_cache_dir": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tradingagents/dataflows/data_cache"),
                "online_tools": False,
                "llm_provider": "openai",
                "deep_think_llm": "gpt-4o-mini",
                "quick_think_llm": "gpt-4o-mini",
                "backend_url": "https://api.openai.com/v1"
            }
            
            # Merge with agent config if provided
            if agent_config:
                safe_config.update(agent_config)
            
            self.simulator = BacktestSimulator(config=safe_config, debug=debug)
            
            # Calculate capital per ticker
            capital_per_ticker = initial_capital / len(tickers)
            
            # Run backtest for each ticker
            for i, ticker in enumerate(tickers):
                if self.should_stop:
                    if log_callback:
                        log_callback("Backtest stopped by user")
                    break
                
                # Update progress
                ticker_progress = i / len(tickers)
                if progress_callback:
                    progress_callback(ticker_progress, f"Processing {ticker}...", ticker)
                
                if log_callback:
                    log_callback(f"Starting backtest for {ticker}")
                
                try:
                    # Run single ticker backtest
                    result = self.simulator.run_backtest(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=capital_per_ticker,
                        slippage=slippage
                    )
                    
                    # Calculate metrics
                    metrics = calculate_performance_metrics(result, risk_free_rate)
                    
                    # Create output directory
                    output_dir = os.path.join("./backtest/results", datetime.now().strftime("%Y%m%d_%H%M%S"))
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Generate plots if requested
                    chart_paths = {}
                    if generate_plots:
                        if log_callback:
                            log_callback(f"Generating charts for {ticker}")
                        chart_paths = create_backtest_report(result, ticker, output_dir)
                    
                    # Save metrics to JSON
                    metrics_dict = {
                        'ticker': ticker,
                        'total_return': metrics.total_return,
                        'annualized_return': metrics.annualized_return,
                        'max_drawdown': metrics.max_drawdown,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'sortino_ratio': metrics.sortino_ratio,
                        'win_rate': metrics.win_rate,
                        'total_trades': metrics.total_trades,
                        'winning_trades': metrics.winning_trades,
                        'losing_trades': metrics.losing_trades,
                        'avg_win': metrics.avg_win,
                        'avg_loss': metrics.avg_loss,
                        'profit_factor': metrics.profit_factor,
                        'calmar_ratio': metrics.calmar_ratio,
                        'volatility': metrics.volatility
                    }
                    
                    metrics_path = os.path.join(output_dir, f"{ticker}_metrics.json")
                    with open(metrics_path, 'w') as f:
                        json.dump(metrics_dict, f, indent=2)
                    
                    # Save trades if requested
                    trades_path = None
                    if save_trades and result.trades:
                        trades_path = os.path.join(output_dir, f"{ticker}_trades.csv")
                        self._save_trades_to_csv(result.trades, trades_path)
                    
                    # Store results
                    results[ticker] = {
                        'metrics': metrics_dict,
                        'initial_capital': capital_per_ticker,
                        'final_value': result.final_portfolio_value,
                        'charts': chart_paths,
                        'files': {
                            'metrics_json': metrics_path,
                            'trades_csv': trades_path
                        }
                    }
                    
                    if log_callback:
                        log_callback(f"Completed {ticker}: Return={metrics.total_return:.2f}%, Sharpe={metrics.sharpe_ratio:.2f}")
                    
                except Exception as e:
                    logger.error(f"Error backtesting {ticker}: {str(e)}")
                    if log_callback:
                        log_callback(f"ERROR: Failed to backtest {ticker}: {str(e)}")
                    if debug:
                        logger.error(traceback.format_exc())
                
                # Update progress
                ticker_progress = (i + 1) / len(tickers)
                if progress_callback:
                    progress_callback(ticker_progress, f"Completed {ticker}", ticker)
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0, "Backtest completed", "")
            
            if log_callback:
                log_callback("Backtest completed successfully")
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            if log_callback:
                log_callback(f"ERROR: {str(e)}")
            if debug:
                logger.error(traceback.format_exc())
            raise
        
        finally:
            self.is_running = False
        
        return results
    
    def stop_backtest(self):
        """Stop the running backtest."""
        self.should_stop = True
    
    def _save_trades_to_csv(self, trades: List[Any], filepath: str):
        """Save trade list to CSV file."""
        import pandas as pd
        
        trade_data = []
        for trade in trades:
            trade_data.append({
                'date': trade.date.strftime('%Y-%m-%d'),
                'action': trade.action,
                'price': trade.price,
                'shares': trade.shares,
                'cash_after': trade.cash_after,
                'portfolio_value': trade.portfolio_value
            })
        
        df = pd.DataFrame(trade_data)
        df.to_csv(filepath, index=False)
    
    def get_example_config(self) -> Dict[str, Any]:
        """Get an example configuration for reference."""
        return {
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 30000.0,
            "slippage": 0.001,  # 0.1%
            "risk_free_rate": 0.02,  # 2%
            "save_trades": True,
            "generate_plots": True,
            "debug": False,
            "agent_config": {
                "llm_provider": "openai",
                "quick_think_llm": "gpt-4o-mini",
                "deep_think_llm": "o4-mini-2025-04-16",
                "max_debate_rounds": 1,
                "max_risk_discuss_rounds": 1,
                "online_tools": False
            }
        }