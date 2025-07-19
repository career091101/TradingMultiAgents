#!/usr/bin/env python3
"""
Command-line interface for running backtests.

This module provides a CLI tool to run backtests using the TradingAgents framework.
"""

import argparse
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.simulator import BacktestSimulator
from backtest.metrics import calculate_performance_metrics, format_metrics_report
from backtest.plotting import create_backtest_report
from backtest.validation import ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run backtests using the TradingAgents framework'
    )
    
    # Required arguments
    parser.add_argument(
        'tickers',
        nargs='+',
        help='Stock ticker symbol(s) to backtest (e.g., AAPL MSFT GOOGL)'
    )
    
    parser.add_argument(
        '--start',
        '-s',
        required=True,
        help='Start date for backtest (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--end',
        '-e',
        required=True,
        help='End date for backtest (YYYY-MM-DD format)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--capital',
        '-c',
        type=float,
        default=10000.0,
        help='Initial capital amount (default: $10,000)'
    )
    
    parser.add_argument(
        '--slippage',
        type=float,
        default=0.0,
        help='Slippage percentage as decimal (e.g., 0.001 for 0.1%%, default: 0)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to custom config JSON file for TradingAgents'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='./backtest/results',
        help='Output directory for results (default: ./backtest/results)'
    )
    
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Skip generating plots'
    )
    
    parser.add_argument(
        '--save-trades',
        action='store_true',
        help='Save detailed trade log to CSV'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode for verbose output'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Enable fast mode (minimal agents, no debates)'
    )
    
    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.02,
        help='Annual risk-free rate for Sharpe ratio calculation (default: 0.02)'
    )
    
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {str(e)}")
        return None


def save_trade_log(result, output_path: str):
    """Save detailed trade log to CSV file."""
    import pandas as pd
    
    # Convert trades to DataFrame
    trade_data = []
    for trade in result.trades:
        trade_data.append({
            'date': trade.date.strftime('%Y-%m-%d'),
            'action': trade.action,
            'price': trade.price,
            'shares': trade.shares,
            'cash_after': trade.cash_after,
            'portfolio_value': trade.portfolio_value
        })
    
    df = pd.DataFrame(trade_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Trade log saved to: {output_path}")


def save_metrics_json(metrics, ticker: str, output_dir: str):
    """Save metrics to JSON file for programmatic access."""
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
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"{ticker}_metrics_{timestamp}.json")
    
    with open(json_path, 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    
    logger.info(f"Metrics saved to: {json_path}")


def run_single_backtest(simulator: BacktestSimulator, ticker: str, args) -> None:
    """Run backtest for a single ticker."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running backtest for {ticker}")
    logger.info(f"{'='*60}")
    
    try:
        # Run the backtest
        result = simulator.run_backtest(
            ticker=ticker,
            start_date=args.start,
            end_date=args.end,
            initial_capital=args.capital,
            slippage=args.slippage
        )
        
        # Calculate performance metrics
        metrics = calculate_performance_metrics(result, args.risk_free_rate)
        
        # Print metrics report
        print(format_metrics_report(metrics, ticker))
        
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Save metrics to JSON
        save_metrics_json(metrics, ticker, args.output)
        
        # Save trade log if requested
        if args.save_trades:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trade_log_path = os.path.join(args.output, f"{ticker}_trades_{timestamp}.csv")
            save_trade_log(result, trade_log_path)
        
        # Generate plots if not disabled
        if not args.no_plots:
            create_backtest_report(result, ticker, args.output)
        
        logger.info(f"Backtest completed successfully for {ticker}")
        
    except ValidationError as e:
        logger.error(f"Validation error for {ticker}: {str(e)}")
        # Don't print traceback for validation errors
    except Exception as e:
        logger.error(f"Failed to backtest {ticker}: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()


def main():
    """Main entry point for the backtest runner."""
    args = parse_arguments()
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate dates
    try:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        
        if start_date >= end_date:
            logger.error("Start date must be before end date")
            sys.exit(1)
            
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    # Load custom config if provided
    config = None
    if args.config:
        config = load_config(args.config)
        if config is None:
            logger.warning("Failed to load custom config, using defaults")
    
    # Initialize simulator
    logger.info("Initializing backtest simulator...")
    simulator = BacktestSimulator(config=config, debug=args.debug, fast_mode=args.fast)
    
    # Run backtests for each ticker
    if len(args.tickers) == 1:
        # Single ticker backtest
        run_single_backtest(simulator, args.tickers[0], args)
    else:
        # Portfolio backtest
        logger.info(f"Running portfolio backtest for {len(args.tickers)} tickers")
        
        for ticker in args.tickers:
            run_single_backtest(simulator, ticker, args)
        
        # TODO: Add portfolio-level summary statistics
        logger.info("\nPortfolio backtest completed")
    
    logger.info(f"\nAll results saved to: {args.output}")


if __name__ == '__main__':
    main()