#!/usr/bin/env python3
"""
Verify decision making process
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig
from backtest2.core.engine import BacktestEngine

# Setup very detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Focus on orchestrator and decision making
logging.getLogger('backtest2.agents.orchestrator').setLevel(logging.DEBUG)
logging.getLogger('backtest2.core.engine').setLevel(logging.DEBUG)

async def verify_decisions():
    """Verify decision making with detailed logging"""
    
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 5),  # Just a few days
        initial_capital=100000.0,
        debug=True
    )
    
    print("=== DECISION VERIFICATION ===")
    
    # Create engine with debug hooks
    engine = BacktestEngine(config)
    
    # Hook into orchestrator to log decisions
    original_make_decision = engine.agent_orchestrator.make_decision
    decision_count = 0
    
    async def logged_make_decision(*args, **kwargs):
        nonlocal decision_count
        decision_count += 1
        print(f"\n[DECISION {decision_count}] Making decision with args: {kwargs.get('symbol', 'unknown')}")
        
        result = await original_make_decision(*args, **kwargs)
        
        print(f"[DECISION {decision_count}] Result:")
        print(f"  - Action: {result.action}")
        print(f"  - Confidence: {result.confidence}")
        print(f"  - Quantity: {result.quantity}")
        print(f"  - Rationale: {result.rationale[:100]}..." if result.rationale else "No rationale")
        
        return result
    
    engine.agent_orchestrator.make_decision = logged_make_decision
    
    # Run backtest
    try:
        result = await engine.run()
        print(f"\n=== SUMMARY ===")
        print(f"Total decisions: {decision_count}")
        print(f"Total trades: {result.metrics.total_trades}")
        print(f"Final value: ${result.final_value:,.2f}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set API keys
    import os
    os.environ['OPENAI_API_KEY'] = "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"
    os.environ['FINNHUB_API_KEY'] = "d1p1c79r01qi9vk226a0d1p1c79r01qi9vk226ag"
    
    asyncio.run(verify_decisions())