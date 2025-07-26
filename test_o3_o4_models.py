#!/usr/bin/env python3
"""
Test with o3 and o4-mini models
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig
from backtest2.core.engine import BacktestEngine

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress JSON serialization errors
logging.getLogger('backtest2.agents.llm_client').setLevel(logging.WARNING)

async def test_o3_o4():
    """Test with o3 and o4-mini models"""
    
    print("=== O3/O4 MODEL TEST ===")
    
    # Create LLM config with o3/o4 models
    llm_config = LLMConfig(
        deep_think_model="o3-2025-04-16",
        quick_think_model="o4-mini-2025-04-16",
        temperature=1.0,  # Must be 1.0 for o3/o4 models
        max_tokens=2000
    )
    
    # Create agent config
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    # Create backtest config
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print(f"Deep think model: {llm_config.deep_think_model}")
    print(f"Quick think model: {llm_config.quick_think_model}")
    print(f"Temperature: {llm_config.temperature}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    # Track decisions
    decisions = []
    original_make_decision = engine.agent_orchestrator.make_decision
    
    async def track_decision(*args, **kwargs):
        result = await original_make_decision(*args, **kwargs)
        decisions.append({
            'date': kwargs.get('date'),
            'action': result.action.value,
            'confidence': result.confidence
        })
        return result
    
    engine.agent_orchestrator.make_decision = track_decision
    
    try:
        print("\n=== RUNNING BACKTEST ===")
        result = await engine.run()
        
        print("\n=== RESULTS ===")
        print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
        print(f"Total return: {result.metrics.total_return:.2%}")
        print(f"Total trades: {result.metrics.total_trades}")
        
        # Count decision types
        from collections import Counter
        action_counts = Counter(d['action'] for d in decisions)
        print(f"\n=== DECISION SUMMARY ===")
        for action, count in action_counts.items():
            print(f"{action}: {count}")
        
        if result.transactions:
            print("\n=== TRANSACTIONS ===")
            for i, tx in enumerate(result.transactions[:5]):
                print(f"{i+1}. {tx.timestamp}: {tx.action.value} {tx.quantity:.2f} {tx.symbol} @ ${tx.price:.2f}")
        else:
            print("\n⚠️  No transactions executed")
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_o3_o4())