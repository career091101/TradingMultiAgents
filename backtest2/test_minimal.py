"""Minimal test script for Backtest2"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from backtest2.core.config import BacktestConfig, TimeRange, LLMConfig
from backtest2.core.engine import BacktestEngine


async def run_minimal_test():
    """Run minimal backtest test"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test configuration
    config = BacktestConfig(
        name="minimal_test",
        symbols=["AAPL"],  # Single symbol for testing
        time_range=TimeRange(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 7)  # One week test
        ),
        initial_capital=100000,
        max_positions=5,
        position_limits={
            "AGGRESSIVE": 0.3,
            "NEUTRAL": 0.2,
            "CONSERVATIVE": 0.1
        },
        llm_config=LLMConfig(
            provider="mock",
            deep_thinking_model="mock-o1",
            fast_thinking_model="mock-gpt4o",
            temperature=0.7,
            max_tokens=1000
        ),
        data_sources=["finnhub", "yahoo"],
        reflection_config={
            "enabled": True,
            "levels": ["DAILY", "WEEKLY"],
            "triggers": ["TIME_BASED", "EVENT_BASED"]
        },
        result_dir=Path("results/minimal_test")
    )
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    try:
        print(f"Starting minimal backtest: {config.name}")
        print(f"Symbol: {config.symbols[0]}")
        print(f"Period: {config.time_range.start} to {config.time_range.end}")
        print(f"Initial capital: ${config.initial_capital:,.2f}")
        print("-" * 50)
        
        # Run backtest
        result = await engine.run()
        
        # Display results
        print("\nBacktest Complete!")
        print("-" * 50)
        print(f"Final portfolio value: ${result.final_portfolio_value:,.2f}")
        print(f"Total return: {result.total_return:.2%}")
        print(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
        print(f"Max drawdown: {result.max_drawdown:.2%}")
        print(f"Total trades: {result.trade_count}")
        
        if result.trades:
            print("\nRecent trades:")
            for trade in result.trades[-5:]:  # Last 5 trades
                print(f"  {trade.timestamp}: {trade.action} {trade.quantity} {trade.symbol} @ ${trade.price:.2f}")
        
        # Save results
        result_path = result.save_results()
        print(f"\nResults saved to: {result_path}")
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_minimal_test())