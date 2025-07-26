#!/usr/bin/env python3
"""
Debug script to trace backtest execution flow
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_run():
    """Run backtest with detailed debugging"""
    
    # Create config with debug enabled
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),  # Use past dates
        end_date=datetime(2024, 1, 31),
        initial_capital=100000.0,
        debug=True  # Enable debug mode
    )
    
    print("=== BACKTEST DEBUG START ===")
    print(f"Config: {config}")
    print(f"Symbols: {config.symbols}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add debug logging to time manager
    print(f"\n=== TIME MANAGER DEBUG ===")
    print(f"Start date: {engine.time_manager.start_date}")
    print(f"End date: {engine.time_manager.end_date}")
    print(f"Trading days: {len(engine.time_manager.trading_days)}")
    if engine.time_manager.trading_days:
        print(f"First trading day: {engine.time_manager.trading_days[0]}")
        print(f"Last trading day: {engine.time_manager.trading_days[-1]}")
    else:
        print("WARNING: No trading days generated!")
    
    # Add hooks to trace execution
    original_process = engine._process_symbol
    call_count = 0
    
    async def traced_process(symbol, date):
        nonlocal call_count
        call_count += 1
        print(f"\n[TRACE {call_count}] Processing {symbol} on {date}")
        try:
            result = await original_process(symbol, date)
            print(f"[TRACE {call_count}] Completed {symbol}")
            return result
        except Exception as e:
            print(f"[TRACE {call_count}] ERROR: {e}")
            raise
    
    engine._process_symbol = traced_process
    
    # Run backtest
    try:
        print("\n=== STARTING BACKTEST ===")
        result = await engine.run()
        print(f"\n=== BACKTEST COMPLETED ===")
        print(f"Total process calls: {call_count}")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"\n=== BACKTEST FAILED ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_run())