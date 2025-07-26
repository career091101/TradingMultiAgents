#!/usr/bin/env python3
"""
Debug the engine execution flow
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Enable detailed debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_engine_flow.log')
    ]
)

# Patch the engine to add more debug logging
original_run = BacktestEngine.run
async def debug_run(self):
    """Wrapped run method with debug logging"""
    print(f"\n=== DEBUG: Engine.run() called ===")
    print(f"Symbols: {self.config.symbols}")
    print(f"Time range: {self.config.time_range}")
    print(f"Time manager has {len(list(self.time_manager.trading_days()))} trading days")
    
    # List trading days
    days = list(self.time_manager.trading_days())
    print(f"First 5 trading days: {days[:5]}")
    print(f"Last 5 trading days: {days[-5:]}")
    
    result = await original_run(self)
    print(f"\n=== DEBUG: Engine.run() completed ===")
    return result

BacktestEngine.run = debug_run

# Patch _process_trading_day
original_process = BacktestEngine._process_trading_day
async def debug_process(self, current_date, symbols):
    """Wrapped process method with debug logging"""
    print(f"\n--- Processing {current_date} for {symbols} ---")
    result = await original_process(self, current_date, symbols)
    print(f"--- Completed {current_date} ---")
    return result

BacktestEngine._process_trading_day = debug_process

async def test_engine():
    """Test the engine execution"""
    print("=== ENGINE FLOW DEBUG TEST ===")
    
    # Create config
    llm_config = LLMConfig(
        deep_think_model="mock",
        quick_think_model="mock"
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    # Use explicit TimeRange
    time_range = TimeRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 10)
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print(f"\nConfig created:")
    print(f"  Symbols: {config.symbols}")
    print(f"  Time range: {config.time_range}")
    print(f"  Debug: {config.debug}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    print("\nRunning backtest...")
    result = await engine.run()
    
    print(f"\nResult type: {type(result)}")
    print(f"Final portfolio value: ${result.final_portfolio.total_value:,.2f}")
    print(f"Total trades: {result.metrics.total_trades}")
    
    # Check transactions
    if hasattr(engine, 'transactions'):
        print(f"Transaction buffer length: {len(engine.transactions)}")

if __name__ == "__main__":
    asyncio.run(test_engine())