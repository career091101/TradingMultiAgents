#!/usr/bin/env python3
"""
Test with mock mode - fixed version
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
    
    # Create mock LLM config
    llm_config = LLMConfig(
        deep_think_model="mock",
        quick_think_model="mock"
    )
    
    # Create agent config with mock LLM
    agent_config = AgentConfig(
        llm_config=llm_config
    )
    
    # Create backtest config - ensure agent_config is set
    config = BacktestConfig(
        symbols=["AAPL"],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        initial_capital=100000.0,
        agent_config=agent_config,  # Important!
        debug=True
    )
    
    print("=== MOCK BACKTEST TEST ===")
    print(f"Symbols: {config.symbols}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    print(f"Agent LLM: {config.agent_config.llm_config.deep_think_model}")
    
    # Create and run engine
    engine = BacktestEngine(config)
    
    # Add decision tracking
    original_make_decision = engine.agent_orchestrator.make_decision
    decisions = []
    
    async def track_decision(*args, **kwargs):
        result = await original_make_decision(*args, **kwargs)
        decisions.append({
            'symbol': kwargs.get('symbol'),
            'action': result.action,
            'confidence': result.confidence,
            'quantity': result.quantity
        })
        return result
    
    engine.agent_orchestrator.make_decision = track_decision
    
    try:
        print("\n=== Running backtest ===")
        result = await engine.run()
        
        print("\n=== Results ===")
        # Check result structure
        if hasattr(result, 'final_portfolio'):
            print(f"Final value: ${result.final_portfolio.total_value:,.2f}")
        elif hasattr(result, 'metrics') and hasattr(result.metrics, 'final_value'):
            print(f"Final value: ${result.metrics.final_value:,.2f}")
        else:
            print(f"Result type: {type(result)}")
            print(f"Result attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
        
        if hasattr(result, 'metrics'):
            print(f"Total return: {result.metrics.total_return:.2%}")
            print(f"Total trades: {result.metrics.total_trades}")
        
        print(f"\n=== Decisions Made ===")
        print(f"Total decisions: {len(decisions)}")
        
        # Count decision types
        from collections import Counter
        action_counts = Counter(d['action'].value for d in decisions)
        for action, count in action_counts.items():
            print(f"  {action}: {count}")
        
        if result.transactions:
            print("\n=== First 5 Transactions ===")
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
    # No API keys needed for mock mode
    import os
    os.environ.pop('OPENAI_API_KEY', None)  # Remove if exists
    
    asyncio.run(test_mock())