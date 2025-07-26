#!/usr/bin/env python3
"""
Test backtest with mock mode to bypass LLM issues
"""

import asyncio
import logging
from datetime import datetime
from backtest2.core.config import BacktestConfig, LLMConfig, AgentConfig
from backtest2.core.engine import BacktestEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_mock():
    """Test with mock LLM"""
    
    # Create config with mock LLM
    llm_config = LLMConfig(
        deep_think_model="mock",
        quick_think_model="mock",
        temperature=0.7,
        max_tokens=2000
    )
    
    agent_config = AgentConfig(
        llm_config=llm_config,
        max_debate_rounds=1,
        max_risk_discuss_rounds=1
    )
    
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        initial_capital=100000.0,
        agent_config=agent_config,
        debug=True
    )
    
    print("=== MOCK BACKTEST TEST ===")
    print(f"Config: {config.name}")
    print(f"Symbols: {config.symbols}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    print(f"LLM: {llm_config.deep_think_model}")
    print(f"Agent config LLM: {config.agent_config.llm_config.deep_think_model if config.agent_config else 'No agent config'}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    try:
        print("\n=== Running backtest ===")
        result = await engine.run()
        
        print("\n=== Results ===")
        print(f"Final value: ${result.final_value:,.2f}")
        print(f"Total return: {result.metrics.total_return:.2%}")
        print(f"Total trades: {result.metrics.total_trades}")
        
        if result.transactions:
            print("\n=== Transactions ===")
            for i, tx in enumerate(result.transactions[:5]):
                print(f"{i+1}. {tx.timestamp}: {tx.action} {tx.quantity} {tx.symbol} @ ${tx.price:.2f}")
        else:
            print("\nNo transactions executed")
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock())