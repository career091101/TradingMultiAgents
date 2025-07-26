#!/usr/bin/env python3
"""
Deep debug of execution flow
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig, TimeRange

# Enable ALL debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Monkey-patch to trace agent decisions
from backtest2.agents.orchestrator import AgentOrchestrator

original_make_decision = AgentOrchestrator.make_decision
decision_count = 0

async def trace_make_decision(self, **kwargs):
    global decision_count
    decision_count += 1
    print(f"\n=== DECISION #{decision_count} ===")
    print(f"Date: {kwargs.get('date')}")
    print(f"Symbol: {kwargs.get('symbol')}")
    
    # Check market data
    market_data = kwargs.get('market_data')
    if market_data:
        print(f"Market Data: Close=${market_data.close}, Volume={market_data.volume}")
    else:
        print("Market Data: None")
    
    # Check portfolio
    portfolio = kwargs.get('portfolio')
    if portfolio:
        print(f"Portfolio: Cash=${portfolio.cash}, Positions={len(portfolio.positions)}")
    else:
        print("Portfolio: None")
    
    result = await original_make_decision(self, **kwargs)
    
    print(f"Decision Result: {result.action if result else 'None'}")
    if result and hasattr(result, 'confidence'):
        print(f"Confidence: {result.confidence}")
    if result and hasattr(result, 'rationale'):
        print(f"Rationale: {result.rationale}")
    
    return result

AgentOrchestrator.make_decision = trace_make_decision

async def deep_debug():
    # Create minimal config with mock
    llm_config = LLMConfig(
        deep_think_model="mock",
        quick_think_model="mock"
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    time_range = TimeRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 3)
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        time_range=time_range,
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print("=== DEEP DEBUG FLOW ===")
    print(f"Date range: {time_range.start} to {time_range.end}")
    
    from backtest2.core.engine import BacktestEngine
    engine = BacktestEngine(config)
    
    # Check time manager
    print(f"\nTrading days: {len(engine.time_manager.trading_days)}")
    for i, day in enumerate(engine.time_manager.trading_days):
        print(f"  Day {i+1}: {day}")
    
    result = await engine.run()
    
    print(f"\n=== FINAL RESULT ===")
    print(f"Total decisions made: {decision_count}")
    print(f"Total trades: {result.metrics.total_trades}")
    print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
    
    # Check transactions
    if hasattr(engine, 'transactions'):
        print(f"\nTransactions in buffer: {len(engine.transactions)}")
        if len(engine.transactions) > 0:
            print("First transaction:", engine.transactions.get_all()[0])

if __name__ == "__main__":
    asyncio.run(deep_debug())