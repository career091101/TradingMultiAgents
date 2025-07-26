#!/usr/bin/env python3
"""
Trace the execution flow to find where decisions are being made
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange
from backtest2.core.engine import BacktestEngine

# Setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trace_execution.log'),
        logging.StreamHandler()
    ]
)

# Monkey-patch to add tracing
original_process_symbol = BacktestEngine._process_symbol

async def traced_process_symbol(self, symbol, current_date):
    print(f"\n>>> _process_symbol called: {symbol} on {current_date}")
    result = await original_process_symbol(self, symbol, current_date)
    print(f"<<< _process_symbol completed: {symbol}")
    return result

BacktestEngine._process_symbol = traced_process_symbol

# Trace orchestrator
from backtest2.agents.orchestrator import AgentOrchestrator
original_make_decision = AgentOrchestrator.make_decision

async def traced_make_decision(self, *args, **kwargs):
    print(f"\n>>> make_decision called with: date={kwargs.get('date')}, symbol={kwargs.get('symbol')}")
    result = await original_make_decision(self, *args, **kwargs)
    print(f"<<< make_decision returned: {result.action if result else 'None'}")
    return result

AgentOrchestrator.make_decision = traced_make_decision

async def trace_flow():
    print("=== EXECUTION FLOW TRACE ===")
    
    # Create config with o3/o4
    llm_config = LLMConfig(
        deep_think_model="o3-2025-04-16",
        quick_think_model="o4-mini-2025-04-16",
        temperature=1.0
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    # Use a short date range for testing
    time_range = TimeRange(
        start=datetime(2025, 7, 1),
        end=datetime(2025, 7, 3)
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print(f"\nConfig:")
    print(f"  Symbols: {config.symbols}")
    print(f"  Date range: {time_range.start} to {time_range.end}")
    print(f"  Models: {llm_config.deep_think_model} / {llm_config.quick_think_model}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    print("\n--- Starting backtest ---")
    try:
        result = await engine.run()
        print(f"\n--- Backtest completed ---")
        print(f"Total trades: {result.metrics.total_trades}")
        print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
        
        # Check if any decisions were made
        if hasattr(engine, 'agent_orchestrator'):
            print(f"\nChecking orchestrator state...")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(trace_flow())