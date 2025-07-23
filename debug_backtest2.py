#!/usr/bin/env python3
"""
Debug script to test backtest2 execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_backtest():
    """Test backtest execution with debug logging"""
    
    # Create minimal config
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() - timedelta(days=1),
        initial_capital=100000,
        llm_config=LLMConfig(
            deep_think_model="mock",  # Use mock for testing
            quick_think_model="mock",
            temperature=0.7,
            max_tokens=2000
        )
    )
    
    print(f"Config created: {config}")
    print(f"Time range: {config.start_date} to {config.end_date}")
    
    # Create engine
    engine = BacktestEngine(config)
    print(f"Engine created: {engine}")
    
    # Run backtest
    try:
        print("Starting backtest...")
        result = await engine.run()
        print(f"Backtest completed. Result type: {type(result)}")
        
        if hasattr(result, 'metrics'):
            print(f"Metrics: {result.metrics}")
            if hasattr(result.metrics, 'total_return'):
                print(f"Total return: {result.metrics.total_return}")
        
        if hasattr(result, 'trades'):
            print(f"Number of trades: {len(result.trades) if result.trades else 0}")
            
    except Exception as e:
        print(f"Error during backtest: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(engine, 'cleanup'):
            await engine.cleanup()

if __name__ == "__main__":
    asyncio.run(test_backtest())